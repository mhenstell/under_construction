import time
import logging as log

class Wave:

    WAVE_PERIOD = 10

    def __init__(self, start, direction, speed):
        self.lights = [0] * 10
        self.last_tick = 0
        self.offset = 0
        self.start = start
        self.direction = direction
        self.speed = speed
        self.last_output = [0]*10
        self.run = True

    def __iter__(self):
        return self

    def __next__(self):

        #      Positive offset limit                    Negative offset limit
        while (self.offset < (10 - self.start) + 1) or ((self.start - self.offset) + 2 > 0):

            if time.time() - self.last_tick <= (self.speed / 100):
                return self.last_output
            else:
                log.debug("Start: %s Offset: %s", self.start, self.offset)
                
                marker = (self.start - self.offset) if self.direction < 0 else (self.start + self.offset)

                # Set each light level according to their distance from the marker
                for light in range(0, 10):
                    
                    dist = abs(marker - light)

                    mult = 1.1 - (dist / 1.1)
                    
                    level = int(255 * mult)
                    if level > 255: level = 255
                    elif level < 0: level = 0

                    self.lights[light] = level
                    # print(self.lights)
                
                self.offset += 0.1
                self.last_tick = time.time()
                self.last_output = self.lights
                return self.lights
        self.run = False
        raise StopIteration