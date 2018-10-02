import time
import logging as log 

class Light:

    address = None
    light_level = 0
    update = True

    def __init__(self, address):
        self.address = address

        self.last_startup = 0
        self.last_heard = 0
        self.num_heartbeats = 0
        self.num_startups = 0
        self.dropped = 0
        self.last_sequence = -1

    def set_level(self, level):
        if level != self.light_level:
            self.update = True
        self.light_level = level

    def __repr__(self):
        return "<Light @ %s (%s)>" % (self.address, self.light_level)

    def heartbeat(self, sequence):

        if self.last_sequence < 0:
            self.last_sequence = sequence

        time_since = time.time() - self.last_heard
        self.last_heard = time.time()
        self.num_heartbeats += 1
        
        delta = (sequence - self.last_sequence) % 256
        
        if delta > 0:
            self.dropped += (delta - 1)
            # log.warning("dropped: %s", self.dropped)
        self.last_sequence = sequence
        
    def startup(self):
        self.last_startup = time.time()
        self.num_startups += 1

    def statistics(self):
        should_have = int(time.time() - self.last_startup)
        got = should_have - self.dropped
        loss = (got / should_have) * 100

        return {"heartbeats": self.num_heartbeats, "startups": self.num_startups, "dropped": self.dropped, "loss": loss}