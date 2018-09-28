import time
import logging as log
from collections import defaultdict
from enum import Enum
import random

from common import *
from ripple import Ripple
from wave import Wave
from keepaway import Keepaway

TOUCH_THRESHOLD = 200
CAL_THRESHOLD = 5
CYCLE_PERIOD = 0.05

class Mode(Enum):
    RIPPLE = 0
    WAVE = 1
    KEEPAWAY = 2

# Keep track of trigger/untrigger time for effect speed
class ProxEvent:
    trigger_duration = 0.5 # Maximum

    def __init__(self, address):
        self.address = address
        self.trigger_time = time.time()

    def untrigger(self):
        duration = time.time() - self.trigger_time
        self.trigger_duration = duration if duration < 0.5 else 0.5
        # log.info("Updated duration to %s", self.trigger_duration)

class Controller:

    def __init__(self, transceivers, lights):

        self.lights = lights
        self.transceivers = transceivers
        
        self.first_cycle = True

        self.patterns = []
        self.patterns_by_address = defaultdict(list)
        self.output_stack = [[0]*10]

        self.touch_route_to = None

        self.last_wave = 0

        self.mode = Mode.RIPPLE
        self.keepawayInstance = None

        self.last_cycle = 0


    def __str__(self):
        return repr(self)

    def tick(self):

        if time.time() - self.last_cycle > CYCLE_PERIOD:
            self.processPatterns()

            lights = []
            for light in self.lights:
                lights.append(light.light_level)

            address = BROADCAST
            command = COMMANDS_NAME["ALL_LEVEL"]
            payload = bytearray(lights)

            for transceiver in self.transceivers:
                transceiver.transmit(address, command, lights)

            self.last_cycle = time.time()

        # if time.time() - self.last_wave > 100:
        #     self.effects[0].append(Wave(-3, 1, 3))
        #     self.last_wave = time.time()


        self.checkMode()

    def checkMode(self):

        if (self.first_cycle):
            if self.mode == Mode.KEEPAWAY:
                event = ProxEvent(random.randrange(0, 10))
                ka = Keepaway(event)
                self.keepawayInstance = ka
                self.patterns.append(ka)


        if self.mode == Mode.KEEPAWAY:
            self.touch_route_to = self.keepawayInstance.newTouch
        elif self.mode == Mode.RIPPLE:
            self.touch_route_to = Ripple

        self.first_cycle = False

    def processPatterns(self):
        # Get the next output for each effect running
        # for address in self.patterns:
        #     for effect in self.effects[address]:
        update = False
        for pattern in self.patterns:
            try:
                output = next(pattern)
                if output is not None:
                    log.debug("Got output %s" % output)

                    self.output_stack.append(output)
                    update = True

            except StopIteration:
                log.debug("Pattern finished")
                # self.effects[address].remove(effect)
                self.patterns.remove(pattern)
                self.patterns_by_address[pattern.start].remove(pattern)

        # Set the light level for each light for each output in the stack
        if update:
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
        
        state = True if payload in (b'\xff', 255) else False        
        log.info("Controller touch event for %s (%s) payload: %s", address, state, payload)
        
        # We registered a new touch event
        if state is True:
            log.info("Touch trigger on %s", address)
            event = ProxEvent(address)
            start_time = (time.time() * (1 / CYCLE_PERIOD)) / (1 / CYCLE_PERIOD)
            pattern = self.touch_route_to(event, start_time)

            if self.mode == Mode.RIPPLE:
                self.patterns.append(pattern)
                self.patterns_by_address[address].append(pattern)

        # Ending a touch event
        else:
            log.info("Touch untrigger on %s", address)
            try:
                self.patterns_by_address[address][-1].event.untrigger()
            except IndexError:
                pass
      
    def light_level(self, addr, payload):
        pass

    def heartbeat(self, addr, payload):
        log.info("Received hearbeat from %s", payload)
        pass


