import logging as log
from queue import Queue
import time
import threading
import serial

import controller

def parseUCPacket(data):
    addr = data >> 24
    command = data >> 16 & 0xFF
    payload = data & 0xFFFF
    return addr, command, payload

class Receiver:

    rx_thread = None
    port = None
    controller = None
    run = True

    def __init__(self, port):
        self.port = port

        self.rx_thread = threading.Thread(target=self.reader)
        self.rx_thread.start()

    def reader(self):
        first_line = True

        while self.run is True:
            # data = str(self.port.readline(), encoding="ascii")
            # print(data)
            data = self.port.readline()
            
            # Throw away first line
            if first_line:
                first_line = False
                continue
            if controller is not None:
                data = str(data, encoding="ascii")
                if data[0] is not '#':
                    log.debug("Serial debug: %s", data.strip())
                    continue
                
                addr, command, payload = parseUCPacket(int(data[1:]))

                self.controller.received_message(addr, command, payload)
        self.port.close()

    def stop(self):
        log.info("Closing serial connection")
        self.run = False
        
    def register_controller(self, controller):
        self.controller = controller

class Transceiver:

    device = None
    receiver = None
    port = None

    def __init__(self, device):
        self.device = device
        self.port = serial.Serial(self.device)

        self.receiver = Receiver(self.port)

    def stop(self):
        self.receiver.stop()

    def register_controller(self, controller):
        self.receiver.register_controller(controller)

    def transmit(self, address, command, payload):
        log.info("Transmitting: %s %s %s", address, command, payload)

        output = address << 24
        output += command << 16
        
        # Swap byte order for 16 bit payload
        output += (payload & 0xFF) << 8
        output += (payload >> 8)

        output_bytes = (output).to_bytes(4, byteorder='big')

        log.info("Bytes: %s", output_bytes)

        self.port.write(output_bytes)
        self.port.write(b"\x0a")


if __name__ == "__main__":

    # serial_queue = Queue();

    # port = serial.Serial('/dev/tty.usbmodem541391')
    # serial_thread = threading.Thread(target=readline, args=(port, serial_queue,))
    # serial_thread.start()

    rx = Transceiver('/dev/tty.usbmodem541391')
