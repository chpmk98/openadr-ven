# A simple VEN class to test the functionality of the abstract class in ven.py.

import time
from ven import VEN

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

if __name__ == "__main__":
    a_test_ven = TestVEN()
    a_test_ven.run()
    print("Done.")
