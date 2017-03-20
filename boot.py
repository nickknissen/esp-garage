# Copyright(c) 2017 by craftyguy "Clayton Craft" <clayton@craftyguy.net>
# Distributed under GPLv3+ (see COPYING) WITHOUT ANY WARRANTY.

from machine import Pin

# Config (change these!!!)
SSID = ""
PASSWORD = ""

def do_connect():
    import network
    s_if = network.WLAN(network.STA_IF)
    a_if = network.WLAN(network.AP_IF)
    if a_if.active():
        a_if.active(False)
    if not s_if.isconnected():
        print('connecting to WiFi network...')
        s_if.active(True)
        s_if.connect(SSID, PASSWORD)
        while not s_if.isconnected():
            pass
    print('Network configuration:', s_if.ifconfig())

do_connect()

import main
