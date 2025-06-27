# This file is executed on every boot (including wake-boot from deepsleep)

# From the original boot.py
#import webrepl
#webrepl.start()

## Supposedly this helps keep ampy from dying
import esp
import machine
esp.osdebug(None)
repl_button = machine.Pin(34, machine.Pin.IN, machine.Pin.PULL_UP)

## Set up our network connection
import network
import utime
sta_if = network.WLAN(network.WLAN.IF_STA)
if sta_if.isconnected():
    print("Connected to network!")
else:
    print("Connecting to Wi-Fi..")
    import wifi_credentials
    sta_if.active(True)
    sta_if.connect(wifi_credentials.WIFI_SSID, wifi_credentials.WIFI_PASS)

    # Wait until we successfully connect to Wi-Fi.
    while not sta_if.isconnected():
        # If button 1 is pressed, drop to REPL
        if repl_button.value() == 0:
            raise Exception("Dropping to REPL (while waiting for Wi-Fi connection)")
        utime.sleep_ms(100)
    print("Wi-Fi successfully connected!")

## Check to see if micropython-mdns libraries exist.
import os
import mip
try:
    os.stat("/lib/mdns_client")
except OSError:
    # Install micropython-mdns libraries if needed.
    print("Installing micropython-mdns..")
    mip.install("github:cbrand/micropython-mdns")
    print("micropython-mdns successfully installed!")

## Check if other libraries exist.
try:
    import typing
except ImportError:
    print("Installing typing..")
    mip.install("github:josverl/micropython-stubs/mip/typing.mpy")
    print("typing successfully installed!")

# I think that's all the setup we need!