import logging as log

from controller import Controller
from common import *
import redis

REDIS_CHANNEL = 'uc'

class Transceiver:

    rx_thread = None
    controller = None
    rrredis = None

    def __init__(self):
        self.rrredis = redis.StrictRedis()
        p = self.rrredis.pubsub()
        p.subscribe(**{REDIS_CHANNEL: self.receive_message})
        self.rx_thread = p.run_in_thread(sleep_time=0.001)

    def register_controller(self, controller):
        self.controller = controller

    def stop(self):
        self.rx_thread.stop()

    def receive_message(self, message: dict):
        data: str = message["data"]
        address, command, payload = str(data, encoding="ascii").split(":")
        command = COMMANDS_NAME[command]
        address, command, payload = [int(x) for x in [address, command, payload]]
        self.controller.received_message(address, command, payload)

    def transmit(self, address, command, payload):
        log.debug("xmit %s %s %s", address, command, payload)
        xmit_string = ":".join([str(address), str(COMMANDS[command]), str(payload)])

        log.debug("Transmitting %s", xmit_string)
        self.rrredis.publish(REDIS_CHANNEL, xmit_string)