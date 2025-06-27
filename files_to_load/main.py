# Do print statements work?

import time
from ven import ESP32VEN
import machine

# An ESP32 VEN class.
class TestVEN(ESP32VEN):
    # Operates on the events for our selected program.
    def _operate_on_program_events(self):
        if self.events is None:
            print("No events found.")
        else:
            print("Current events:\n{}".format(self.events))
#             print("Found {} event(s):".format(self.events.num_events()))
#             for an_event in self.events:
#                 print("Program ID: {}, Event ID: {}, Intervals: \n{}\n\n".format(an_event.getProgramId(), an_event.getId(), an_event.getIntervals()))

    # Waits until an appropriate time to grab the next program.
    def _wait(self):
        # If button is pressed, drop to REPL
        if self.repl_button.value() == 0:
            raise Exception("Dropping to REPL")
        
        # Otherwise, just sleep for five seconds.
        time.sleep(5)

if __name__ == "__main__":
    a_test_ven = TestVEN() # Automatically connects to the first local VTN-RI and first available program without user input.
    a_test_ven.run()
    print("Done.")


