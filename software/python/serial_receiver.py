import logging as log
from queue import Queue
import time
import threading
import serial


class Receiver:

    rx_thread = None
    device = None
    port = None

    def __init__(self, device):
        self.device = device
        self.port = serial.Serial(self.device)

        self.rx_thread = threading.Thread(target=self.reader)
        self.rx_thread.start()

    def reader(self):
        while True:
            data = self.port.readline()

    def stop(self):
        log.info("Closing serial connection")
        self.rx_thread.stop()
        self.port.close()



if __name__ == "__main__":

    # serial_queue = Queue();

    # port = serial.Serial('/dev/tty.usbmodem541391')
    # serial_thread = threading.Thread(target=readline, args=(port, serial_queue,))
    # serial_thread.start()

    rx = Receiver('/dev/tty.usbmodem541391')
