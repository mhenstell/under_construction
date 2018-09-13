import logging as log
from common import *



class Controller:

    pattern = None
    transceiver = None

    def __init__(self, transceivers, pattern):

        self.pattern = pattern
        self.transceivers = transceivers

    def __str__(self):
        return repr(self)

    def tick(self):
        self.pattern.tick()

        try:
            update = self.pattern.updates.pop()
            log.debug("Update: %s", update)

            # xmit_message = ":".join([str(update.address), "output", str(update.light_level)])
            # print(xmit_message)
            # self.transceiver.transmit(xmit_message)

            address = update.address
            command = COMMANDS_NAME["LIGHT_LEVEL"]
            payload = update.light_level
            
            for transceiver in self.transceivers:
                transceiver.transmit(address, command, payload)
        except IndexError:
            pass

    def received_message(self, address: int, command: int, payload: int):
        # command, data = message.split(":")
        # log.info("Received %s command (%s)", command, data)

        cmd_func = getattr(self, COMMANDS[command].lower())
        cmd_func(address, payload)

    def prox(self, addr, payload):
        self.pattern.prox_event(addr, payload)

    def light_level(self, addr, payload):
        pass


