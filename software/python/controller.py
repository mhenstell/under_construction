import logging as log
from common import *

TOUCH_THRESHOLD = 2000
CAL_THRESHOLD = 5

class Controller:

    def __init__(self, transceivers, pattern):

        self.pattern = pattern
        self.transceivers = transceivers
        
        self.cycle = 0
        self.freq_zero = 0
        self.freq_cal = 0
        self.cal_max = 0
        self.touch_state = False


    def __str__(self):
        return repr(self)

    def tick(self):
        self.pattern.tick()

        try:
            update = self.pattern.updates.pop()
            address = update.address
            command = COMMANDS_NAME["LIGHT_LEVEL"]
            payload = update.light_level
            
            for transceiver in self.transceivers:
                transceiver.transmit(address, command, payload)
        except IndexError:
            pass

    def received_message(self, address: int, command: int, payload: int):
        cmd_func = None
        try:
            cmd_func = getattr(self, COMMANDS[command].lower())
        except KeyError:
            log.error("Received invalid packet: <Addr: %s Cmd: %s Payload: %s>", address, command, payload)

        if cmd_func:
            cmd_func(address, payload)

    def prox_data(self, addr, payload):

        # log.info("Prox %s: %s", addr, payload)
        self.cycle += 1

        if self.cycle < 10:
            return

        if self.cycle == 10:
            # log.info("Prox startup")
            self.freq_zero = payload
            self.freq_cal = payload

        if self.cycle % 20 == 0:
            # log.info("Autocalibration")
            if self.cal_max < CAL_THRESHOLD:
                self.freq_zero = payload
            self.freq_cal = payload
            self.cal_max = 0

        self.cal_max = max(abs(payload - self.freq_cal), self.cal_max)

        freq = abs(payload - self.freq_zero)
        touch = True if freq > TOUCH_THRESHOLD else False
        
        log.debug("Frequency %s Touch %s", freq, touch)

        if touch != self.touch_state:
            self.pattern.touch_event(addr, touch)
            self.touch_state = touch
        
      
    def light_level(self, addr, payload):
        pass

    def heartbeat(self, addr, payload):
        log.info("Received hearbeat from %s", payload & 0xFF)


