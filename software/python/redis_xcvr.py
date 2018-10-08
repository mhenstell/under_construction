import time
import logging as log
from collections import defaultdict

from controller import Controller
from common import *
import redis

REDIS_CHANNEL = 'uc'

RAMP_UP = 1
HOLD = 2
RAMP_DOWN = 3
INACTIVE = 4

TICK_PERIOD = 0.1
RAMP_TIME_MULT = 4

class Effect:
    def __init__(self, trigger):
        self.trigger = trigger
        self.mode = RAMP_UP
        self.start_time = time.time()

class Transceiver:

    rx_thread = None
    rrredis = None

    def __init__(self):
        self.rx_callback = None

        self.rrredis = redis.StrictRedis()
        p = self.rrredis.pubsub()
        p.subscribe(**{REDIS_CHANNEL: self.receive_message})

        self.lastTick = 0
        self.effects = defaultdict(list)


        self.rx_thread = p.run_in_thread(sleep_time=0.001)

    def register_callback(self, callback):
        self.rx_callback = callback

    def stop(self):
        log.warning("Stopping redis thread")
        self.rx_thread.stop()

    def receive_message(self, message: dict):
        data: str = message["data"]
        # address, command, payload = str(data, encoding="ascii").split(":")
        split = str(data, encoding="ascii").split(":")
        address, command = split[0], split[1]
        
        # log.debug("ADDR %s CMD %s PAY %s", address, command, data)

        if int(address) == BROADCAST:
            return

        payload = split[2]
        
        command = COMMANDS_NAME[command]
        address, command, payload = [int(x) for x in [address, command, payload]]
        self.rx_callback(address, command, payload)

    def transmit(self, address, command, payload):
        # log.info("xmit %s %s %s", address, command, payload)
        if address < 0: return

        if type(payload) == list:
            payload = ":".join([str(x) for x in payload])

        xmit_string = ":".join([str(address), str(COMMANDS[command]), str(payload)])

        # log.debug("Transmitting %s", xmit_string)
        self.rrredis.publish(REDIS_CHANNEL, xmit_string)

    def transmitTrigger(self, trigger):

        self.effects[trigger.light_id].append(Effect(trigger))

    # def tick(self):
        
    #     if time.time() - self.lastTick < TICK_PERIOD:
    #         return

    #     levels = defaultdict(list)

    #     for address in self.effects:
    #         for effect in self.effects[address]:
                
    #             rampUpTime = effect.trigger.ramp_up  * RAMP_TIME_MULT
    #             holdTime = effect.trigger.hold * RAMP_TIME_MULT
    #             rampDownTime = effect.trigger.ramp_down * RAMP_TIME_MULT
    #             effectTime = (time.time() - effect.start_time) * 1000

    #             if rampUpTime == 0:
    #                 rampUpTime = 1
    #             if rampDownTime == 0:
    #                 rampDownTime = 1

    #             if effect.mode == RAMP_UP:
    #                 percent = effectTime / rampUpTime
    #                 if percent > 1:
    #                     levels[effect.trigger.light_id] = effect.trigger.level
    #                     effect.mode = HOLD
    #                 else:
    #                     levels[effect.trigger.light_id] = effect.trigger.level * percent

    #             elif effect.mode == HOLD:
    #                 levels[effect.trigger.light_id] = effect.trigger.level
    #                 if effectTime > (rampUpTime + holdTime):
    #                     effect.mode = RAMP_DOWN

    #             elif effect.mode == RAMP_DOWN:
    #                 percent = (effectTime - rampUpTime - holdTime) / rampDownTime
    #                 if percent > 1:
    #                     levels[effect.trigger.light_id] = 0
    #                     effect.mode = INACTIVE
    #                 else:
    #                     levels[effect.trigger.light_id] = effect.trigger.level * (1 - percent)

    #     for address in levels:
    #         self.transmit(address, COMMANDS_NAME["LIGHT_LEVEL"], int(levels[address]))


    #     self.lastTick = time.time()

    def tick(self):
        pass