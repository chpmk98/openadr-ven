# Do print statements work?

import utime
import machine

# Supposedly this is needed to allow re-flashing without clearing all memory.
repl_button = machine.Pin(34, machine.Pin.IN, machine.Pin.PULL_UP)

"""
This example runs a constant service discovery for google chromecast services.
It prints them out if they are added, changed or removed.

As this method stores local state, like service records for refreshing the state
it requires more memory than the one time discovery. However, depending on your use
case it might be better to use this instead of the one time query.
"""

import network
import uasyncio

from mdns_client import Client
# from mdns_client.responder import Responder

from mdns_client.service_discovery import ServiceResponse
from mdns_client.service_discovery.txt_discovery import TXTServiceDiscovery

wlan = network.WLAN(network.STA_IF)
## We already do all this in boot.py, I think..
# wlan.active(True)
# wlan.connect("<SSID>", "<Password>")
# while not wlan.isconnected():
#     import time
# 
#     time.sleep(1.0)

assert wlan.isconnected(), "Network isn't actually connected smh"
own_ip_address = wlan.ifconfig()[0]

loop = uasyncio.get_event_loop()
client = Client(own_ip_address)

""" From service_responder.py
# Currently does not seem to work properly.
responder = Responder(
    client,
    own_ip=lambda: own_ip_address,
    host=lambda: "my-awesome-microcontroller-{}".format(responder.generate_random_postfix()),
)


def announce_service():
    # If button 1 is pressed, drop to REPL
    if repl_button.value() == 0:
        raise Exception("Dropping to REPL (inside announce_service() function)")
    responder.advertise("_myawesomeservice", "_tcp", port=12345, data={"some": "metadata", "for": ["my", "service"]})
    # If you want to set a dedicated service host name
#     responder.advertise(
#         "_myawesomeservice",
#         "_tcp",
#         port=12345,
#         data={"some": "metadata", "for": ["my", "service"]},
#         service_host_name="specialcontrollerservicename",
#     )


announce_service()

# If button 1 is pressed, drop to REPL
if repl_button.value() == 0:
    raise Exception("Dropping to REPL (before loop.run_forever() function)")

loop.run_forever()

# """

# """ From service_discovery_constant.py
discovery = TXTServiceDiscovery(client)


class ServiceMonitor:
    def service_added(self, service: ServiceResponse) -> None:
        print("Service added: {}".format(service))

    def service_updated(self, service: ServiceResponse) -> None:
        print("Service updated: {}".format(service))

    def service_removed(self, service: ServiceResponse) -> None:
        print("Service removed: {}".format(service))


async def discover():
    discovery.add_service_monitor(ServiceMonitor())
    await discovery.query("_airplay", "_tcp")

    await uasyncio.sleep(20)


loop.run_until_complete(discover())
print(discovery.current("_airplay", "_tcp"))
# """

while True:
    # If button 1 is pressed, drop to REPL
    if repl_button.value() == 0:
        raise Exception("Dropping to REPL (after loop.run_forever() function)")
    # Do nothing
    utime.sleep_ms(100)

