# An abstract class for a VEN load, along with several example implementations.
# Each non-abstract VEN must implement their own response to the received price.

from abc import ABC, abstractmethod
import json

import socket
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser, ServiceStateChange
from oadr30.vtn import VTNOps

import time

# An abstract VEN class.
class VEN(ABC):
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

    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # mDNS self-advertisements 
    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    
    # Advertises itself as a VEN over mDNS for local discovery.
    def _start_mDNS_advertisements(self):
        # Get the local IP address(es)
        local_IPs = socket.gethostbyname_ex(socket.gethostname())[-1]
        boring_IPs = ['127.0.0.1', '192.168.56.1'] # We do not care about these IP addresses
        local_IPs = list(set(local_IPs) - set(boring_IPs)) # Should give us the useful IP addresses
        
        # Get DNS-SD advertisement information from our config.
        self.openadr_version = self._get_config("OpenADR version")
        self.dnssd = self._get_config("DNS-SD")
        self.dnssd_type = self.dnssd["type"]
        self.dnssd_name = self.dnssd["name"]
        self.dnssd_port = self.dnssd["port"]
        self.dnssd_txt = self.dnssd["txt"] if "txt" in self.dnssd else None
        
        # Put together a DNS-SD service advertisement and start running it.
        self.zeroconf = Zeroconf()
        desc = {"OpenADR {}".format(self.openadr_version): None,
                "version": self.openadr_version, 
                "role":"ven",
                "documentation":"https://www.openadr.org/openadr-3-0",}
        if self.dnssd_txt is not None:
            desc.update(self.dnssd_txt)
        self.wsInfo = ServiceInfo('{}.local.'.format(self.dnssd_type),
                                  "{}.{}.local.".format(self.dnssd_name, self.dnssd_type),
                                  server="{}.local.".format(self.dnssd_name.replace(" ", "-")),
                                  addresses=[socket.inet_aton(an_IP) for an_IP in local_IPs],
                                  port=self.dnssd_port,
                                  properties=desc)
        self.zeroconf.register_service(self.wsInfo) # Start advertising.
    
    # Unregisters itself as a VEN.
    def _stop_mDNS_advertisements(self):
        # Do stuff based on the above method.
        self.zeroconf.unregister_service(self.wsInfo)
        self.zeroconf.close()


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
        # Otherwise, we assume that a_VTN is a dictionary with "addresses":list, "port":int, "base URL":string.
        for an_address in a_VTN["addresses"]:
            VTN_IP = socket.inet_ntoa(an_address)
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
    # In this case, we ask the user for input.
    def _use_this_VTN(self, name, info):
        # Notify that we found something.
        print("Local VTN server '{}' found with address(es) {} at port {}.".format(name, info.addresses, info.port))
        go_nogo = input("Would you like to connect to '{}'? [y/n] ".format(name))
        while go_nogo not in ("y", "n"):
            go_nogo = input("Sorry, I do not know what '{}' means.\nPlease enter 'y' to connect, or enter 'n' to keep looking for another VTN: ".format(go_nogo, name))
        
        # If we do not want to connect to this VTN, then we ignore it.
        return go_nogo == "y"
    
    # Parses connection information out of the VTN mDNS advertisements.
    # Returns a dictionary with the appropriate fields, to be ingested by self._attempt_connection().
    def _parse_VTN_advertisement(self, name, info):
        # We grab its local IP, port number, and base URL.
        a_VTN = {
            "addresses": info.addresses,
            "port": info.port,
            "base URL": info.properties[b"base_url"].decode("utf-8") # Assumes UTF-8 encoding.
        }
        return a_VTN
    
    # For browsing through local VTNs.
    def _on_service_found(self, zeroconf, service_type, name, state_change):
        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                # If this thing is NOT a VTN, then we ignore it.
                if info.properties[b"role"] != b"vtn":
                    return
                
                # If we do not want to connect to this VTN, then we ignore it.
                if not self._use_this_VTN(name, info):
                    print("Rejecting local VTN '{}'. Continuing to look for other local VTNs...")
                    return
                
                # Parse out the VTN connectivity information from the mDNS advertisement.
                a_VTN = self._parse_VTN_advertisement(name, info)
                
                # Connect to the VTN.
                self._attempt_connection(a_VTN)
                # If we failed to connect, we continue looking.
                if self.vtn is None:
                    print("Failed connecting to local VTN '{}.' Continuing to look for other local VTNs...")
                    return
                
                # Otherwise we successfully connected to a VTN and can close the browser.
                zeroconf.close()

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
            # If we didn't instantiate self.dnssd for DNS-SD advertisements, do so now.
            if not self.advertise:
                self.dnssd = self._get_config("DNS-SD")
                self.dnssd_type = self.dnssd["type"]
            # Instantiate a Zeroconf for the browser
            browser_zeroconf = Zeroconf()
            self.browser = ServiceBrowser(browser_zeroconf, "{}.local.".format(self.dnssd_type), handlers=[self._on_service_found])
            # Wait until we find something.
            while self.vtn is None:
                time.sleep(0.1)
        # Once we get to this point, we should be successfully connected to a VTN, so we can just return.


    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # Program and Events selection
    # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    
    # What to do when there are no events on the VTN.
    # Returns True to continue searching, False to break out and return.
    def _no_programs_try_again(self):
        input("No programs found on this VTN. Press <Enter> to try again. ")
        return True
        
    # Selects the desired program from a list of programs called program_list.
    # Returns the 0-indexed index of the desired program in the list.
    def _get_desired_program_index(self, program_list):
        print("Found {} programs! Which one do you want?".format(program_list.num_programs()))
        for an_ind, a_program in enumerate(program_list, start=1):
            print("[{}] Program ID: {}, Program Name: {}, Country: {}, Program Type: {}".format(an_ind, a_program.getId(), a_program["programName"], a_program["country"], a_program["programType"]))
        selected_ind = int(input())-1
        while selected_ind < 0 or selected_ind >= len(program_list):
            selected_ind = int(input("'{}' not valid. Please enter an integer between 1 and {}: ".format(selected_ind, len(program_list))))-1
        return selected_ind
    
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
            self.program_id = self.program.getId()
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
    @abstractmethod
    def _operate_on_program_events(self):
        pass
    
    # Waits until an appropriate time to grab the next set of events.
    # This method will change, depending on the specific VEN.
    @abstractmethod
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
        
         
         
         
         
         
         
         
         
         
         
         
         
         
                