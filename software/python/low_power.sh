#!/bin/bash
set -x
sudo tvservice --off
echo 0 > /sys/bus/usb/devices/1-1.1.1/bConfigurationValue
echo 0 > /sys/bus/usb/devices/1-1.1/bConfigurationValue
sudo ifconfig eth0 down
sudo ifconfig wlan0 down