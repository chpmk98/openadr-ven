# An abstract class for a VEN load, along with several example implementations.
# Each non-abstract VEN must implement their own response to the received price.

# from abc import ABC, abstractmethod
import json

# import socket
# from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser, ServiceStateChange
from oadr30.vtn import VTNOps

import time
import machine

import network
import uasyncio

from mdns_client import Client
from mdns_client.service_discovery import ServiceResponse
from mdns_client.service_discovery.txt_discovery import TXTServiceDiscovery

# An abstract VEN class.
# Written in MicroPython for the Olimex ESP32-POE board.
class ESP32VEN: #(ABC):
    # A helper function to get key-value items from config files.
    def _get_config(self, key, none_ok=False):
        if key in self.config:
            # Return the value in the main configuration file if it exists.
            return self.config[key]
        elif (self.default_config is not None) and (key in self.default_config):
            # Otherwise, return the value in the backup/default configuration file if it exists.
            return self.default_config[key]
        
        # If we are ok with having a None value, we return None.
        if none_ok:
            return None
        else:
            # Raise an error if the key does not exist.
            raise KeyError("{} does not exist in the provided configuration file(s).".format(key))
    
    # Instantiate a VEN with some configurations.
    def __init__(self, json_path=None): 
        if json_path is None:
            default_json_path = "./configs/default.json"
            print("No config file provided for the VEN. Using {} by default.".format(default_json_path))
            json_path = default_json_path # Use this as our default config file.
        with open(json_path) as config_file:
            self.config = json.load(config_file)
        # Add in an option to have a default JSON file.
        if "default JSON" in self.config:
            with open(self.config["default JSON"]) as default_config_file:
                self.default_config = json.load(default_config_file)
        else:
            self.default_config = None
        # Maybe we want some sanity checks here to make sure everything we need is available?
        self.vtn = None
        self.zeroconf = None
        self.program_id = self._get_config("program ID", none_ok=True)
        # This is needed to allow re-flashing without clearing all memory.
        self.repl_button = machine.Pin(34, machine.Pin.IN, machine.Pin.PULL_UP)
        # This is for mDNS.
        self.wlan = network.WLAN(network.STA_IF)
        assert self.wlan.isconnected(), "Network isn't connected."
        self.own_ip_address = self.wlan.ifconfig()[0]
        self.loop = uasyncio.get_event_loop()
        self.client = Client(self.own_ip_address)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # mDNS self-advertisements 
    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    
    # Advertises itself as a VEN over mDNS for local discovery.
    def _start_mDNS_advertisements(self):
        # This is theoretically possible with the cbrand/micropython-mdns library,
        # but not critical for proper VEN functioning.
        pass
    
    # Unregisters itself as a VEN.
    def _stop_mDNS_advertisements(self):
        pass

    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # HTTP(S) connection to the VTN 
    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    
    # A basic connection, given one full URL.
    # If the connection succeeds, then store the VTN object in self.vtn. Otherwise, set self.vtn to None.
    def _connect_to_full_URL(self, a_full_URL):
        try:
            print("Connecting to {}...".format(a_full_URL))
            # For the VTN-RI
            self.vtn = VTNOps(a_full_URL, self.ven["client_id"], self.ven["client_secret"])
        except:
            print("Could not connect to {}.".format(a_full_URL))
            self.vtn = None
    
    # Iterates through IP addresses for a particular VTN and attempts connection.
    def _attempt_connection(self, a_VTN):
        # Checks if a_VTN contains a full URL. If so, establish a connection directly.
        if "full URL" in a_VTN:
            self._connect_to_full_URL(a_VTN["full URL"])
            # Exit if we successfully connected. Otherwise, continue attempting connections.
            if self.vtn is not None:
                print("Successfully connected to {}!".format(a_VTN["full URL"]))
                return
        # Otherwise, we assume that a_VTN is a dictionary with "addresses":list[str], "port":int, "base URL":string.
        for VTN_IP in a_VTN["addresses"]:
#             VTN_IP = socket.inet_ntoa(an_address)
            VTN_full_url = "http://{}:{}{}".format(VTN_IP, a_VTN["port"], a_VTN["base URL"])
            self._connect_to_full_URL(VTN_full_url)
            # Exit the loop if we successfully connected. Otherwise, continue attempting connections.
            if self.vtn is not None:
                print("Successfully connected to {}!".format(VTN_full_url))
                return

    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # Local VTN service discovery (DNS-SD) over mDNS 
    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    
    # How we select the "correct" VTNs. Returns True to connect, False to continue looking.
    # In this case, we automatically attempt a connection.
    def _use_this_VTN(self, service_response):
        # Wait two seconds, because this behaves poorly if the server is just spinning up.
        time.sleep(2)
        return True
    
    # Parses connection information out of the VTN mDNS advertisements.
    # Returns a dictionary with the appropriate fields, to be ingested by self._attempt_connection().
    def _parse_VTN_advertisement(self, service_response):
        # We grab its local IP, port number, and base URL.
        a_VTN = {
            "addresses": list(service_response.ips),
            "port": int(service_response.port),
            "base URL": service_response.txt_records["base_path"][0]
#             "base URL": info.properties[b"base_url"].decode("utf-8") # Assumes UTF-8 encoding.
        }
        return a_VTN
    
#     # For browsing through local VTNs.
#     def _on_service_found(self, zeroconf, service_type, name, state_change):
#         if state_change is ServiceStateChange.Added:
#             info = zeroconf.get_service_info(service_type, name)
#             if info:
#                 # If this thing is NOT a VTN, then we ignore it.
#                 if info.properties[b"role"] != b"vtn":
#                     return
#                 
#                 # If we do not want to connect to this VTN, then we ignore it.
#                 if not self._use_this_VTN(name, info):
#                     print("Rejecting local VTN '{}'. Continuing to look for other local VTNs...")
#                     return
#                 
#                 # Parse out the VTN connectivity information from the mDNS advertisement.
#                 a_VTN = self._parse_VTN_advertisement(name, info)
#                 
#                 # Connect to the VTN.
#                 self._attempt_connection(a_VTN)
#                 # If we failed to connect, we continue looking.
#                 if self.vtn is None:
#                     print("Failed connecting to local VTN '{}.' Continuing to look for other local VTNs...")
#                     return
#                 
#                 # Otherwise we successfully connected to a VTN and can close the browser.
#                 zeroconf.close()

    # Scan for services once.
    async def _discover_VTNs(self):
        print("Scanning for {}.{}".format(self.dnssd_name, self.dnssd_protocol))
        response_list = await self.discovery.query_once(self.dnssd_name, self.dnssd_protocol, timeout=1.0)
        print("Received {} responses.".format(len(response_list)))
        
        # Look through our results.
        for a_response in response_list:
            print("Looking at {}.".format(a_response))
            # If this thing is NOT a VTN, then we ignore it.
            if a_response.txt_records["role"][0] != "vtn":
                print("Not a VTN, so ignoring! Role is {}.".format(a_response.txt_records["role"][0]))
                continue
            
            # If we do not want to connect to this VTN, then we ignore it.
            if not self._use_this_VTN(a_response):
                print("Rejecting local VTN '{}'. Continuing to look for other local VTNs...".format(a_response.name))
                continue
            
            # Parse out the VTN connectivity information from the mDNS advertisement.
            a_VTN = self._parse_VTN_advertisement(a_response)
            print("Parsed advertisement as {}".format(a_VTN))
            
            # Connect to the VTN
            self._attempt_connection(a_VTN)
            # If we failed to connect, we continue looking.
            if self.vtn is None:
                print("Failed connecting to local VTN '{}'. Continuing to look for other local VTNs...".format(a_response.name))
            else:
                # Otherwise, we are done! 
                # We use the first program listed in the advertisement, if not defined in config.
                if self.program_id is None:
                    self.program_id = a_response.txt_records["program_names"].split(",")[0]
                return

    # Browses for a local VTN to connect to.
    def _connect_to_VTN(self):
        # Pull any predefined VTN information from config
        target_VTN = self._get_config("VTN", none_ok=True)
        # Pull this device's predefined VEN client information from config
        self.ven = self._get_config("VEN")
        # If a VTN is already pre-defined, attempt connection
        if target_VTN is not None:
            self._attempt_connection(target_VTN)
        # Otherwise, look for one on local network
        if self.vtn is None:
            print("Looking for a VTN on the local network using DNS-SD...")
#             # If we didn't instantiate self.dnssd for DNS-SD advertisements, do so now.
#             if not self.advertise:
#                 self.dnssd = self._get_config("DNS-SD")
#                 self.dnssd_type = self.dnssd["service_type"]
#             # Instantiate a Zeroconf for the browser
#             browser_zeroconf = Zeroconf()
#             self.browser = ServiceBrowser(browser_zeroconf, "{}.local.".format(self.dnssd_type), handlers=[self._on_service_found])
            # Set up our mDNS service discovery.
            self.dnssd = self._get_config("DNS-SD")
            self.dnssd_name = self.dnssd["service_name"]
            self.dnssd_protocol = self.dnssd["service_protocol"]
            self.discovery = TXTServiceDiscovery(self.client)
            # Wait until we find something.
            while self.vtn is None:
                self.loop.run_until_complete(self._discover_VTNs())
                
                # If REPL button is pressed, drop to REPL
                if self.repl_button.value() == 0:
                    raise Exception("Dropping to REPL")

                time.sleep(2)
        # Once we get to this point, we should be successfully connected to a VTN, so we can just return.


    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # Program and Events selection
    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    
    # What to do when there are no events on the VTN.
    # Returns True to continue searching, False to break out and return.
    # If there are no programs on the VTN, wait for 4 seconds and scan again.
    def _no_programs_try_again(self):
        print("No programs found. Trying again...")
        time.sleep(4)
        return True
    
    # Selects the desired program from a list of programs called program_list.
    # Given a list of available programs, simply select the first one.
    def _get_desired_program_index(self, program_list):
        return 0
    
    # Identifies the program we are planning to operate on, gets it from the VTN, and stores it in self.program.
    def _select_program(self):
        # If there's a desired program_id pre-defined, just grab it.
        if self.program_id is not None:
            self.program = self.vtn.get_program(program_id=self.program_id)
            # If this failed, then we need to redo our program_id lmao.
            if self.program is None:
                print("Failed to find a program with ID '{}' on this VTN. Getting a list of all available programs instead..".format(self.program_id))
                self.program_id = None
        # If we don't know what program we want, look for a list of programs from the VTN and have the user select one.
        if self.program_id is None:
            # Loop until we find programs lmao.
            program_list = []
            while len(program_list) == 0:
                program_list = self.vtn.get_programs()
                if len(program_list) == 0:
                    # If we don't want to try again, we simply return.
                    if not self._no_programs_try_again():
                        return # Alternatively, we could just quit?
            # Once we've found a list of programs, we select the one we want.
            selected_ind = self._get_desired_program_index(program_list)
            self.program = program_list[selected_ind]
            print("Looking at program {}".format(self.program))
            self.program_id = self.program['id'] #.getId()
        print("Using Program ID: {}".format(self.program_id))
    
    # Gets the events for our desired program from the VTN and stores it in self.events.
    def _get_program_events(self):
        # Note: If this fails, self.events will be None.
        self.events = self.vtn.get_events(program_id=self.program_id)


    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # Application-specific methods
    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    
    # Operates on the event stored in self.events. 
    # This method will change, depending on the specific VEN.
#     @abstractmethod
    def _operate_on_program_events(self):
        pass
    
    # Waits until an appropriate time to grab the next set of events.
    # This method will change, depending on the specific VEN.
#     @abstractmethod
    def _wait(self):
        pass

    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # Main operational loop
    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    
    # Run everything as appropriate.
    def run(self):
        # Start mDNS advertisements if desired.
        self.advertise = self._get_config("self-advertise")
        if self.advertise:
            self._start_mDNS_advertisements()
        
        # Connect to a VTN.
        self._connect_to_VTN()
        
        # Confirm the VTN has the desired program (or select a program that is available on the VTN).
        self._select_program()
        
        # While connected, operate forever.
        try:
            while(1):
                # Get the next set of events for this program.
                self._get_program_events()
                
                # Operate on the next program.
                self._operate_on_program_events()
                
                # Wait until a program update is desired.
                self._wait()
        except KeyboardInterrupt:
            pass
        finally:
            if self.advertise:
                print("Unregistering VEN...")
                self._stop_mDNS_advertisements()
        
         
         
         
         
         
         
         
         
         
         
         
         
         
                