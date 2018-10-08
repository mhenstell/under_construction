import time
import logging as log

class Ripple:

    RIPPLE_TIMEOUT = 12

    def __init__(self, event, start_time, frequency):
        self.event = event
        self.lights = [0] * 10
        self.offset = 0
        self.frequency = frequency # Hz
        self.last_tick = start_time - (1 / self.frequency) # hack to get this to run the first tick
        self.start = event.address
        self.exhausted = False
        self.last_output = [0]*10

    def __iter__(self):
        return self

    def __next__(self):

        q = 1

        #      Positive offset limit                    Negative offset limit
        while (self.offset < (10 - self.start) + 1) or ((self.start - self.offset) + 2 > 0):

            # Set the ripple time based on the trigger duration from ProxEvent
            # self.ripple_time = self.event.trigger_duration / 10
            if time.time() - self.last_tick <= (1 / self.frequency):
                return self.last_output
            else:
                # log.info("Event %s", self.event)
                # log.info("%s", self.event.trigger_duration)
                # log.debug("Start: %s Offset: %s", start, offset)
                
                # Calculate the upper and lower edge of the outward ripple
                lower_marker = self.start - self.offset;
                upper_marker = self.start + self.offset;

                # Set each light level according to their distance from
                # the upper or lower marker
                for light in range(0, 10):
                    
                    dist_lower = abs(lower_marker - light)
                    dist_upper = abs(upper_marker - light)
                    mult = 0
                    
                    if dist_lower < q:
                        mult = 1 - dist_lower
                    elif dist_upper < q:
                        mult = 1 - dist_upper
                    level = max(int(255 * mult), 0)

                    self.lights[light] = level
                
                self.offset += 0.1 * (1.5 - (self.event.trigger_duration))
                self.last_tick = time.time()
                self.last_output = self.lights
                return self.lights
        self.exhausted = True
        raise StopIteration