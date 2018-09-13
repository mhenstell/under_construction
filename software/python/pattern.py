import time
import math
import logging as log
from collections import defaultdict

# class Ripple:

#     offset = 0

#     self __init__(self, start, speed):
#         log.debug("Starting ripple at %s with speed %s", start, speed)


def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)


# def ripple(event):
#     offset = 0
#     last_tick = 0
#     lights = [0] * 10
#     ripple_time = 0.05
#     q = 1
#     start = event.address

#     #      Positive offset limit       Negative offset limit
#     while (offset < (10 - start) + 1) or ((start - offset) + 2 > 0):
#         if time.time() - last_tick < ripple_time:
#             yield None
#         else:

#             # log.debug("Start: %s Offset: %s", start, offset)
#             lower_marker = start - offset;
#             upper_marker = start + offset;

#             for light in range(0, 10):
                
#                 dist_lower = abs(lower_marker - light)
#                 dist_upper = abs(upper_marker - light)
#                 mult = 0
                
#                 if dist_lower < q:
#                     mult = 1 - dist_lower
#                 elif dist_upper < q:
#                     mult = 1 - dist_upper
#                 level = int(255 * mult)

#                 lights[light] = level
#             yield lights

#             offset += 0.1
#             last_tick = time.time()
#     return

class Ripple:

    def __init__(self, event):
        self.event = event
        self.lights = [0] * 10
        self.offset = 0
        self.last_tick = 0
        self.start = event.address
        self.ripple_time = 0.05

    def __iter__(self):
        return self

    def __next__(self):

        q = 1

        #      Positive offset limit       Negative offset limit
        while (self.offset < (10 - self.start) + 1) or ((self.start - self.offset) + 2 > 0):

            self.ripple_time = self.event.trigger_duration / 10

            if time.time() - self.last_tick < self.ripple_time:
                return
            else:
                # log.info("Event %s", self.event)
                # log.info("%s %s", self.ripple_time, self.event.trigger_duration)
                # log.debug("Start: %s Offset: %s", start, offset)
                lower_marker = self.start - self.offset;
                upper_marker = self.start + self.offset;

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
        raise StopIteration


class ProxEvent:
    trigger_duration = 0.5 # Maximum

    def __init__(self, address):
        self.address = address
        self.trigger_time = time.time()

    def untrigger(self):
        duration = time.time() - self.trigger_time
        self.trigger_duration = duration if duration < 0.5 else 0.5
        # log.info("Updated duration to %s", self.trigger_duration)

class Pattern:

    lights = None
    updates = []
    effects = defaultdict(list)
    output_stack = [[0]*10]

    events = {}

    def __init__(self, lights):
        self.lights = lights

    def prox_event(self, address, payload):
        log.debug("Pattern prox event for %s (%s)", address, payload)
        
        log.debug("Events: %s", self.events)
        if payload < 12000 and address not in self.events:
                log.debug("Prox trigger on %s", address)
                event = ProxEvent(address)

                self.effects[address].append(Ripple(event))
                self.events[address] = 1

        elif payload > 12000 and address in self.events:
                log.debug("Prox untrigger on %s", address)
                try:
                    self.effects[address][-1].event.untrigger()
                except IndexError:
                    pass
                del self.events[address]

    def tick(self):

        for address in self.effects:
            for effect in self.effects[address]:
                try:
                    output = next(effect)
                    if output is not None:
                        log.debug("Got output %s" % output)

                        self.output_stack.append(output)

                except StopIteration:
                    log.debug("Ripple finished")
                    self.effects[address].remove(effect)

        for light_idx in range(0, 10):
            level = max([output[light_idx] for output in self.output_stack])
            self.lights[light_idx].set_level(level)

        for light in self.lights:
            if light.update is True:
                self.updates.append(light)
                light.update = False

