import logging as log 
class Light:

    address = None
    light_level = 0
    update = True

    def __init__(self, address):
        self.address = address

    def set_level(self, level):
        if level != self.light_level:
            self.update = True
        self.light_level = level

    def __repr__(self):
        return "<Light @ %s (%s)" % (self.address, self.light_level)
