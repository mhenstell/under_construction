from controller import Controller
import redis

LISTEN_CHANNEL = 'uc'

class Receiver:

    rx_thread = None
    controller = None

    def __init__(self, controller: Controller):
        print("Starting redis receiver with controller " + str(controller))

        self.controller = controller

        r = redis.StrictRedis()
        p = r.pubsub()
        p.subscribe(**{LISTEN_CHANNEL: self.receive_message})
        self.rx_thread = p.run_in_thread(sleep_time=0.001)

    def stop(self):
        self.rx_thread.stop()

    def receive_message(self, message: dict):
        data: str = message["data"]
        address, text = str(data, encoding="ascii").split(":")
        self.controller.received_message(address, text)