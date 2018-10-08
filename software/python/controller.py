import time
import logging as log
from collections import defaultdict
from enum import Enum
import random
import json

from common import *
from prox_event import ProxEvent
from ripple import Ripple
from wave import Wave
from keepaway import Keepaway
from alternate import Alternate
from cylon import Cylon

TOUCH_THRESHOLD = 200
CAL_THRESHOLD = 5
CYCLE_HZ = 20
MODE_TIMEOUT = 50

class Mode(Enum):
    RIPPLE = 0
    WAVE = 1
    KEEPAWAY = 2
    ALTERNATE = 3
    CYLON = 4

class Controller:

    def __init__(self, transceivers, lights):
        self.lights = lights
        self.transceivers = transceivers

        self.patterns = []
        # self.patterns_by_address = defaultdict(list)
        self.output_stack = [[0]*10]

        self.touch_route_to = None
        self.last_cycle = 0
        # self.mode = Mode.RIPPLE
        # self.mode = Mode.KEEPAWAY
        # self.mode = Mode.ALTERNATE
        # self.mode = Mode.WAVE
        # self.mode = Mode.CYLON

        self.mode = random.choice(list(Mode))
        self.last_mode_change = time.time()
        log.info("Starting %s", self.mode)
        
        self.keepawayInstance = None
        self.last_wave = 0

        self.priority = False
        self.last_triggered = [0] * 10

    def __str__(self):
        return repr(self)

    def start_keepaway(self):
        event = ProxEvent(random.randrange(0, 10))
        ka = Keepaway(event, CYCLE_HZ)
        self.keepawayInstance = ka
        self.patterns.append(ka)
        self.touch_route_to = self.keepawayInstance.newTouch

    def first_run(self):
        if self.mode == Mode.KEEPAWAY:
            self.start_keepaway()

        elif self.mode == Mode.ALTERNATE:
            self.touch_route_to = self.clear_ripple
            self.start_alternate()

        elif self.mode == Mode.RIPPLE:
            self.touch_route_to = self.ripple

        elif self.mode == Mode.WAVE:
            self.touch_route_to = self.clear_ripple

        elif self.mode == Mode.CYLON:
            self.touch_route_to = self.clear_ripple
            self.start_cylon()

    def handle_wave(self):
        if time.time() - self.last_wave > \
           (random.randrange(int(Wave.WAVE_PERIOD * 0.5), int(Wave.WAVE_PERIOD * 1.5))):

           dir_list = [1] * 20 + [-1] * 10
           direction = random.choice(dir_list)
           w = Wave(0 if direction > 0 else 9, direction, random.randrange(1, 10))
           self.patterns.append(w)
           self.last_wave = time.time()

    def handle_ripple(self):

        if time.time() - max(self.last_triggered) > \
            (random.randrange(int(Ripple.RIPPLE_TIMEOUT * 0.5), int(Ripple.RIPPLE_TIMEOUT * 1.5))):
            addr = random.randrange(0, 9)
            event = ProxEvent(addr)
            start_time = round(time.time() * 20, 0) / 20
            ripple = Ripple(event, start_time, CYCLE_HZ)
            self.patterns.append(ripple)
            self.last_triggered[addr] = time.time()

    def start_cylon(self):
        cy = Cylon(random.randrange(5, 10))
        self.patterns.append(cy)

    def start_alternate(self):
        al = Alternate(CYCLE_HZ)
        self.patterns.append(al)

    def clear_ripple(self, event, start_time, freq=CYCLE_HZ):
        ripple = Ripple(event, start_time, freq)
        self.patterns = [ripple]
        self.mode = Mode.RIPPLE

    def ripple(self, event, start_time, freq=CYCLE_HZ):
        ripple = Ripple(event, start_time, freq)
        self.patterns.append(ripple)

    def checkMode(self):

        # Should change mode?
        if time.time() - self.last_mode_change > \
           (MODE_TIMEOUT + random.randrange(int(MODE_TIMEOUT * 0.75), int(MODE_TIMEOUT * 1.25))):
            
            self.mode = random.choice(list(Mode))
            log.info("Changing modes to: %s", self.mode)
            self.last_mode_change = time.time()

            for pattern in self.patterns:
                if type(pattern) != type(Ripple):
                    pattern.run = False

            if self.mode == Mode.KEEPAWAY:
                self.start_keepaway()
            elif self.mode == Mode.RIPPLE:
                self.touch_route_to = Ripple
            elif self.mode == Mode.WAVE:
                self.touch_route_to = self.clear_ripple
            elif self.mode == Mode.CYLON:
                self.touch_route_to = self.clear_ripple
                self.start_cylon()
            elif self.mode == Mode.ALTERNATE:
                self.touch_route_to = self.clear_ripple

        if self.mode == Mode.WAVE:
            self.handle_wave()

        elif self.mode == Mode.RIPPLE:
            self.handle_ripple()

    def tick(self):
        if (time.time() - self.last_cycle > (1 / CYCLE_HZ)) or self.priority:
            if self.priority: log.info("Priority!")
            self.priority = False
            self.processPatterns()

            lights = []
            for light in self.lights:
                lights.append(light.light_level)

            log.debug("Sending lights: %s (%s patterns)", lights, len(self.patterns))

            address = BROADCAST
            command = COMMANDS_NAME["ALL_LEVEL"]
            payload = bytearray(lights)

            for transceiver in self.transceivers.values():
                transceiver.transmit(address, command, lights)

            self.last_cycle = time.time()

        self.checkMode()

    def processPatterns(self):
        # Get the next output for each effect running
        # for address in self.patterns:
        #     for effect in self.effects[address]:
        # update = False
        completed_patterns = []
        for pattern in self.patterns:
            try:
                output = next(pattern)
                if output is not None:
                    log.debug("Received pattern output: %s" % output)

                    self.output_stack.append(output)
                    # update = True
            except StopIteration:
                log.debug("Pattern finished")
                completed_patterns.append(pattern)

        # Remove all the patterns marked as completed
        if len(completed_patterns) > 0:
            log.info("Cleaning up %s completed patterns" % len(completed_patterns))
            for pattern in completed_patterns:
                self.patterns.remove(pattern)
            # if pattern in self.patterns_by_address[pattern.start]:
            #     self.patterns_by_address[pattern.start].remove(pattern)

        # Set the light level for each light for each output in the stack
        # if update:
        for light_idx in range(0, 10):
            level = max([output[light_idx] for output in self.output_stack])
            self.lights[light_idx].set_level(level)
        self.output_stack = [[0] * 10]

    def received_message(self, address, command, payload):
        cmd_func = None
        try:
            cmd_func = getattr(self, COMMANDS[command].lower())
        except KeyError:
            log.error("Received invalid packet: <Addr: %s Cmd: %s Payload: %s>", address, command, payload)

        if cmd_func:
            cmd_func(address, payload)

    def prox_data(self, address, payload):

        log.debug("Prox [%s]: %s", address, payload)

        if "redis" in self.transceivers:
            prox = int.from_bytes(payload, byteorder="big")
            self.transceivers["redis"].transmit(address, COMMANDS_NAME["PROX_SIM"], prox)

    def touch_trig(self, addr, payload):

        if self.touch_route_to == None:
            return

        if time.time() - self.last_triggered[addr] > 0.5:

            log.info("Touch trigger on %s", addr)
            event = ProxEvent(addr)
            start_time = round(time.time() * 20, 0) / 20
            self.touch_route_to(event, start_time, CYCLE_HZ)
            self.priority = True

            self.last_triggered[addr] = time.time()

    def touch_untrig(self, addr, payload):

        # if time.time() - self.last_triggered[addr] > 0.05:

        log.info("Touch untrigger on %s", addr)
        # try:
        #     self.patterns_by_address[addr][-1].event.untrigger()
        # except IndexError:
        #     pass

        for pattern in self.patterns:
            if type(pattern) == type(Ripple) and pattern.start == addr:
                self.pattern.event.untrigger()

        self.last_triggered[addr] = time.time()

    def light_level(self, addr, payload):
        pass

    def heartbeat(self, addr, payload):
        light_num = payload[0]
        if light_num < 0 or light_num > 9: return
        log.info("Received heartbeat from %s: %s", light_num, payload[1])

        self.lights[light_num].heartbeat(payload[1])

    def startup(self, addr, payload):
        light_num = payload[0]
        if light_num < 0 or light_num > 9: return
        log.warning("Received startup from %s", light_num)

        self.lights[light_num].startup()

    def prox_sim(self, addr, payload):
        pass

    def reload(self, addr, payload):
        log.warning("CONFIG RELOAD")

        with open("config.json") as cjfile:
            config = json.load(cjfile)

            for idx, light in config["lights"].items():
                # q = [int(idx), COMMANDS_NAME["SET_CONFIG"], 0xEF, 0xBE, 0]
                output = bytearray([int(idx), COMMANDS_NAME["SET_CONFIG"], 0xEF, 0xBE, 0])
                output += light["RecalThreshold"].to_bytes(2, byteorder="little")
                output += light["TouchThreshold"].to_bytes(2, byteorder="little")
                output += light["RecalCycles"].to_bytes(1, byteorder="little")
                output += light["SendProx"].to_bytes(2, byteorder="little")


                if "serial" in self.transceivers:
                    self.transceivers["serial"].transmitBytes(output)
                    time.sleep(0.1)

    def ack_config(self, addr, payload):
        log.info("ACK Config [%s]: %s", addr, payload)

        rt = payload[4] << 8 | payload[3]
        tt = payload[6] << 8 | payload[5]
        rc = payload[7]

        self.transceivers["redis"].transmit(addr, COMMANDS_NAME["ACK_CONFIG_SIM"], "%s:%s:%s" % (rt, tt, rc))

    def ack_config_sim(self, addr, payload):
        pass

    def all_level(self, addr, payload):
        pass



