import time
import logging as log

class Wave:

    def __init__(self, start, direction, duration):
        self.lights = [0] * 10
        self.last_tick = 0
        self.offset = 0
        self.start = start
        self.direction = direction
        self.duration = duration

    def __iter__(self):
        return self

    def __next__(self):

        q = 3

        #      Positive offset limit                    Negative offset limit
        while (self.offset < (10 - self.start) + 1) or ((self.start - self.offset) + 2 > 0):

            if time.time() - self.last_tick <= (self.duration / 100):
                return
            else:
                log.debug("Start: %s Offset: %s", self.start, self.offset)
                
                marker = (self.start - self.offset) if self.direction < 0 else (self.start + self.offset)

                # Set each light level according to their distance from the marker
                for light in range(0, 10):
                    
                    dist = abs(marker - light)

                    mult = 1.5 - (dist / 1.5)
                    
                    level = int(255 * mult)
                    if level > 255: level = 255
                    elif level < 0: level = 0

                    self.lights[light] = level
                    # print(self.lights)
                
                self.offset += 0.1
                self.last_tick = time.time()
                return self.lights
        raise StopIteration