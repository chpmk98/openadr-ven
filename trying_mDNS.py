# An attempt to use python-zeroconf to do mDNS service advertisement on my LAN,
# in a way that is visible to Discovery.app.

# Copied from https://stackoverflow.com/questions/1916017/simplest-way-to-publish-over-zeroconf-bonjour
from zeroconf import ServiceInfo, Zeroconf, IPVersion
import json
import socket

zeroconf = Zeroconf()
desc = {"version": "3.0.1", 
        "url": "http://192.168.128.1/openadr",
        "role":"vtn",
        "openapi":"http://192.168.128.1/openadr/openapi",
        "OpenADR 3.0.1":None,}
wsInfo = ServiceInfo('_openadr-http._tcp.local.',
                     "My VTN Server._openadr-http._tcp.local.",
                     addresses=[socket.inet_aton("127.0.0.1")],
                     port=8080,
                     properties=desc)
zeroconf.register_service(wsInfo)

import time
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    print("Unregistering...")
    zeroconf.unregister_service(wsInfo)
    zeroconf.close()

''' # My own attempt haha
import zeroconf
import time

# Instantiate a mDNS thingy?
mDNS_boi = zeroconf.Zeroconf()

# Register a service?
openADR_info = zeroconf.ServiceInfo(
        type_="_openadr._https._tcp.local.", # fully qualified service type name
        name="_openadr._https._tcp.local.", # fully qualified service name
        port=443, # port that the service runs on. 443 is web server.
        properties={"version":"3.1"}, # dictionary of properties
        #parsed_addresses=["10.50.237.42"] # I think this is my laptop's current IP address
    )
mDNS_boi.register_service(openADR_info)

# # I think we need a pause somewhere to have the thing continue going.. so..
# input("Press <Enter> to exit..")

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    print("Unregistering...")
    mDNS_boi.unregister_service(openADR_info)
    mDNS_boi.close()
'''