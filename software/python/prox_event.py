import logging as log
import time

# Keep track of trigger/untrigger time for effect speed
class ProxEvent:
    trigger_duration = 0.5 # Maximum

    def __init__(self, address):
        self.address = address
        self.trigger_time = time.time()

    def untrigger(self):
        duration = time.time() - self.trigger_time
        self.trigger_duration = duration if duration < 1 else 1
        log.info("Updated duration to %s", self.trigger_duration)