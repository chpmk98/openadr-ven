# A simple VEN class to test the functionality of the abstract class in ven.py.

import time
from ven import VEN
from oadr30.price_server_client import PriceServerClient

# A simple VEN class.
class TestVEN(VEN):
    # Operates on the events for our selected program.
    def _operate_on_program_events(self):
        if self.events is None:
            print("No events found.")
        else:
            print("Found {} event(s):".format(self.events.num_events()))
            for an_event in self.events:
                print("Program ID: {}, Event ID: {}, Intervals: \n{}\n\n".format(an_event.getProgramId(), an_event.getId(), an_event.getIntervals()))
    
    # Waits until an appropriate time to grab the next program.
    def _wait(self):
        # Just sleep for five seconds.
        time.sleep(5)

# A VEN class that connects to the global Olivine servers.
class OlivineVEN(TestVEN):
    # Don't need a client_id or client_secret when connecting to Olivine servers.
    def _connect_to_full_URL(self, a_full_URL):
        try:
            print("Connecting to {}...".format(a_full_URL))
            # For the Olivine servers
            self.vtn = PriceServerClient(a_full_URL)
        except:
            print("Could not connect to {}.".format(a_full_URL))
            self.vtn = None
    
    # Olivine servers do not have programs.
    def _select_program(self):
        return
    
    # The PriceServerClient has a different API than VTNOps for getting events.
    def _get_program_events(self):
        self.events = self.vtn.getEvents()

# A VEN class that automatically connects to the first local VTN available,
# attempts requesting the "local" program, and selects the first available
# program if "local" does not exist.
class AutoVEN(TestVEN):
    # Automatically connect to the VTN instead of prompting the user.
    def _use_this_VTN(self, name, info):
        # Wait two seconds, because this behaves poorly if the server is just spinning up.
        time.sleep(2)
        return True
    
    # If there are no programs on the VTN, wait for 4 seconds and scan again.
    def _no_programs_try_again(self):
        print("No programs found. Trying again...")
        time.sleep(4)
        return True
    
    # Given a list of available programs, simply select the first one.
    def _get_desired_program_index(self, program_list):
        return 0

if __name__ == "__main__":
    a_test_ven = TestVEN() # Scans and prompts the user while connecting to a local VTN-RI.
    # a_test_ven = OlivineVEN("./configs/olivine.json") # Connects to the global Olivine servers. 
    # a_test_ven = AutoVEN() # Automatically connects to the first local VTN-RI and first available program without user input.
    a_test_ven.run()
    print("Done.")
