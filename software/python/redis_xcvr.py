import logging as log

from controller import Controller
from common import *
import redis

REDIS_CHANNEL = 'uc'

class Transceiver:

    rx_thread = None
    rrredis = None

    def __init__(self):
        self.rx_callback = None

        self.rrredis = redis.StrictRedis()
        p = self.rrredis.pubsub()
        p.subscribe(**{REDIS_CHANNEL: self.receive_message})
        self.rx_thread = p.run_in_thread(sleep_time=0.001)

    def register_callback(self, callback):
        self.rx_callback = callback

    def stop(self):
        log.warning("Stopping redis thread")
        self.rx_thread.stop()

    def receive_message(self, message: dict):
        data: str = message["data"]
        address, command, payload = str(data, encoding="ascii").split(":")
        command = COMMANDS_NAME[command]
        address, command, payload = [int(x) for x in [address, command, payload]]
        self.rx_callback(address, command, payload)

    def transmit(self, address, command, payload):
        # log.debug("xmit %s %s %s", address, command, payload)
        xmit_string = ":".join([str(address), str(COMMANDS[command]), str(payload)])

        # log.debug("Transmitting %s", xmit_string)
        self.rrredis.publish(REDIS_CHANNEL, xmit_string)

    def tick(self):
        pass