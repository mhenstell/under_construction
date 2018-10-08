import math
import time
import logging as log

class Alternate:

    def __init__(self, frequency):
        self.lights = [0] * 10
        self.offset = 0
        self.frequency = frequency # Hz
        start_time = round(time.time() * 20, 0) / 20
        self.last_tick = start_time - (1 / self.frequency) # hack to get this to run the first tick
        self.run = True
        self.last_output = [0]*10

    def __iter__(self):
        return self

    def __next__(self):

        while self.run:

            # Set the ripple time based on the trigger duration from ProxEvent
            if time.time() - self.last_tick <= (1 / self.frequency):
                return self.last_output
            else:
                
                evens = int(math.sin(self.offset) * 255)
                if evens < 0: evens = 0

                odds = int(math.sin(self.offset + math.pi) * 255)
                if odds < 0: odds = 0

                for x in range(0, 10):
                    if x % 2 == 0: self.lights[x] = evens
                    else: self.lights[x] = odds


                self.last_tick = time.time()
                self.last_output = self.lights
                self.offset += 0.1
                return self.lights
        self.run = False
        raise StopIteration