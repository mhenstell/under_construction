import time
import logging as log

class Ripple:

    def __init__(self, event, start_time):
        self.event = event
        self.lights = [0] * 10
        self.offset = 0
        self.last_tick = start_time
        self.start = event.address
        self.ripple_time = 0.05
        self.exhausted = False

        print("start time %s" % self.last_tick)

    def __iter__(self):
        return self

    def __next__(self):

        q = 1

        #      Positive offset limit                    Negative offset limit
        while (self.offset < (10 - self.start) + 1) or ((self.start - self.offset) + 2 > 0):

            # Set the ripple time based on the trigger duration from ProxEvent
            self.ripple_time = self.event.trigger_duration / 10

            if time.time() - self.last_tick < self.ripple_time:
                return
            else:
                # log.info("Event %s", self.event)
                # log.info("%s %s", self.ripple_time, self.event.trigger_duration)
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
                    level = int(255 * mult)

                    self.lights[light] = level
                
                self.offset += 0.1
                self.last_tick = time.time()
                return self.lights
        self.exhausted = True
        raise StopIteration