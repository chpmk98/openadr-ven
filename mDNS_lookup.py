# OK now we try to come up with something that can take a looksee at mDNS and 
# identify any OpenADR items and list them out here.

from zeroconf import ServiceBrowser, Zeroconf, ServiceStateChange

def on_service_found(zeroconf, service_type, name, state_change):
    if state_change is ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)
        if info:
            print("Service found:", name, "at", info.addresses[0], "port", info.port)
            print(info)
            print("This OpenADR object is a {}!".format(info.properties[b"role"]))
            print("This OpenADR's base url is {}!".format(info.properties[b"base_url"]))

if __name__ == '__main__':
    zeroconf = Zeroconf()
    service_type = "_openadr-http._tcp.local."  # Replace with the desired service type
    browser = ServiceBrowser(zeroconf, service_type, handlers=[on_service_found])
        
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        zeroconf.close()


''' # My own attempt ha
from zeroconf import ServiceInfo, Zeroconf

zeroconf = Zeroconf()

desc = {"version": "3.0.1", 
        "url": "http://192.168.128.1/openadr",
        "role":"vtn",
        "openapi":"http://192.168.128.1/openadr/openapi",
        "OpenADR 3.0.1":None,}
wsInfo = ServiceInfo('_http._tcp.local.',
                     "_openadr._http._tcp.local.",
                     addresses=[socket.inet_aton("127.0.0.1")],
                     port=8080,
                     properties=desc)

queried_info = zeroconf.get_service_info("_http._tcp.local.", "_openadr._http._tcp.local.")

print(queried_info)
zeroconf.close()
'''
