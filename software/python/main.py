import sys
import time
import signal
import argparse
import platform
import subprocess
import logging as log
from functools import partial

from controller import Controller
from light import Light

quit = False

lights = [Light(x) for x in range(0, 10)]

def signal_handler(sig, frame, transceivers):
    global quit

    log.warning('You pressed Ctrl+C!')
    quit = True
    
    for transceiver in transceivers.values():
        transceiver.stop()
    try:
        sys.exit(0)
    except:
        pass

def run(args: list):
    log.debug("Running with args: %s", args)

    transceivers = {}

    if args.port is not None:
        import serial_xcvr
        transceivers["serial"] = serial_xcvr.Transceiver(args.port)

    if args.redis:
        import redis_xcvr
        transceivers["redis"] = redis_xcvr.Transceiver()

    cont = Controller(transceivers, lights)

    for transceiver in transceivers.values():
        transceiver.register_callback(cont.received_message)

    log.debug("Registering signal handler")
    handler = partial(signal_handler, transceivers=transceivers)
    signal.signal(signal.SIGINT, handler)


    # Enter low power mode?
    if platform.system() == "Linux":
        log.warning("Linux detected - checking for LP jumper on pins 7 and 9")
        from gpiozero import LED, Button
        led = LED(27)
        jumper = Button(4)

        x = 25
        while jumper.is_pressed:
            led.on()
            time.sleep(0.1)
            led.off()
            time.sleep(0.1)
            x -= 1
            if x == 0: break

        if jumper.is_pressed:
            log.warning("Entering low power mode")
            try:
                subprocess.call(['./low_power.sh'])
            except PermissionError:
                log.exception("Failed to call low power - check permissions")

    log.info("Starting controller")
    cont.first_run()
    while quit is False:
        cont.tick()
        for transceiver in transceivers.values():
            transceiver.tick()
        time.sleep(0.0001)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=str)
    parser.add_argument("-r", "--redis", action="store_true")
    parser.add_argument("-v", "--verbosity", type=str)

    args = parser.parse_args()
    
    log.basicConfig(level=getattr(log, args.verbosity), format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S')

    run(args)