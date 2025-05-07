# A simple VEN class to test the functionality of the abstract class in ven.py.

import time
from ven import VEN
from gpiozero import PWMOutputDevice
from guizero import App, Text

# A simple VEN class.
class DemoVEN(VEN):    
    # Instantiate a VEN with some configurations.
    def __init__(self, json_path=None): 
        super().__init__(json_path)
        # Device-specific parameters. May need to be changed.
        self.low_price = 0.2
        self.high_price = 0.4
        self.low_PWM = 0    # On a scale from 0 to 100
        self.high_PWM = 20  # On a scale from 0 to 100
        # For the PWM.
        self.pin = PWMOutputDevice(18)
        # For the display.
        self.app = App()
        self.text = Text(self.app, text="VEN Initialized!")
        self.app.display()
        
    # Helper function to display text using the App.
    def _display_text(self, a_string):
        self.text.clear()
        self.text.append(a_string)
        self.app.display()

    # Automatically connect to the VTN instead of prompting the user.
    def _use_this_VTN(self, name, info):
        # Wait two seconds, because this behaves poorly if the server is just spinning up.
        time.sleep(2)
        return True

    # If there are no programs on the VTN, wait for 4 seconds and scan again.
    def _no_programs_try_again(self):
        self._display_text("No programs found. Trying again...")
        time.sleep(4)
        return True
    
    # Given a list of available programs, simply select the first one.
    def _get_desired_program_index(self, program_list):
        return 0

    # Operates on the events for our selected program.
    def _operate_on_program_events(self):
        if self.events is None:
            self._display_text("No events found.")
        else:
            # This may change depending on the format of the events loaded on the VTN, but I am assuming
            # that we just read off the first interval of the first event and use that.
            cur_price = self.events[0].getIntervals()[0]
            
            # If the price is low, run the PWM high throttle.
            if cur_price <= self.low_price:
                cur_PWM = self.high_PWM
                cur_mode = "high"
            # If the price is high, run the PWM low throttle.
            elif cur_price >= self.high_price:
                cur_PWM = self.low_PWM
                cur_mode = "low"
            # Otherwise, linearly scale the PWM based on pricing.
            else:
                # I think this is correct..
                cur_PWM = ((self.high_price - cur_price)/(self.high_price - self.low_price))*(self.high_PWM - self.low_PWM) + self.low_PWM
                # If cur_price == self.high_price, then cur_PWM = self.low_PWM.
                # If cur_price == self.low_price, then cur_PWM = self.high_PWM.
                cur_mode = "medium"

            # Set the PWM appropriately.
            self.pin.value = cur_PWM / 100
            
            # Display some text appropriately.
            self._display_text("Current Price: {}\nCurrent Mode: {}\nCurrent PWM: {} percent".format(cur_price, cur_mode, cur_PWM))
    
    # Waits until an appropriate time to grab the next program.
    def _wait(self):
        # Just sleep for ten seconds.
        time.sleep(10)

if __name__ == "__main__":
    a_ven = DemoVEN("./configs/demo.json")
    a_ven.run()
    self._display_text("Done.")
