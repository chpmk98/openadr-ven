#!/usr/bin/env python3

# A simple VEN class to test the functionality of the abstract class in ven.py.

import time
import logging
import pprint
import flask
from flask import Flask, render_template, redirect, url_for, jsonify
from ven import VEN
from operator import itemgetter
from datetime import datetime
from gpiozero import PWMOutputDevice
import wsgiserver
from threading import Thread
from functools import partial

pp = pprint.PrettyPrinter(indent=2)


def get_index_in_variable_interval(seconds_per_step: int) -> int:
    """
    https://chatgpt.com/share/681fb99d-3750-800f-b6da-5f0470e7c629
    """
    if seconds_per_step <= 0:
        raise ValueError("seconds_per_step must be a positive integer")
    interval_length = 24 * seconds_per_step  # Total duration of each interval
    now = datetime.now()
    total_seconds_today = now.hour * 3600 + now.minute * 60 + now.second
    interval_start = (total_seconds_today // interval_length) * interval_length
    seconds_into_interval = total_seconds_today - interval_start
    index = seconds_into_interval // seconds_per_step
    return int(index)


def seconds_until_next_interval(seconds_per_step: int) -> float:
    """
    https://chatgpt.com/share/681fb99d-3750-800f-b6da-5f0470e7c629
    """
    if seconds_per_step <= 0:
        raise ValueError("seconds_per_step must be a positive integer")

    interval_length = 24 * seconds_per_step
    now = datetime.now()
    total_seconds_today = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1_000_000
    next_interval_start = ((total_seconds_today // interval_length) + 1) * interval_length
    seconds_remaining = next_interval_start - total_seconds_today
    return seconds_remaining


def seconds_until_next_step(seconds_per_step: int) -> float:
    if seconds_per_step <= 0:
        raise ValueError("seconds_per_step must be a positive integer")

    now = datetime.now()
    total_seconds_today = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1_000_000
    interval_step_offset = total_seconds_today % seconds_per_step
    seconds_remaining = seconds_per_step - interval_step_offset
    return seconds_remaining


# Example Event
# { 'createdDateTime': '11:48:26',
#   'eventName': 'SpringHDP',
#   'id': '1561',
#   'intervalPeriod': { 'duration': 'PT1H',
#                       'start': '2025-05-09T21:00:00+00:00'},
#   'intervals': [ { 'id': 12,
#                    'payloads': [{'type': 'PRICE', 'values': [0.1385]}]},
#                  { 'id': 13,
#                    'payloads': [{'type': 'PRICE', 'values': [0.1518]}]},
#                  { 'id': 14,
#                    'payloads': [{'type': 'PRICE', 'values': [0.1829]}]},


# A simple VEN class.
class HVAC_VEN(VEN):
    # Instantiate a VEN with some configurations.
    def __init__(self, json_path=None, logger=None):
        super().__init__(json_path, logger=logger)
        self.interval_sleep = 5
        self.interval_id = 0
        self.current_price = 0
        self.current_mode = ""
        self.current_PWM = 0
        # Device-specific parameters. May need to be changed.
        self.low_price = 0.10
        self.high_price = 0.4
        self.low_PWM = 20   # On a scale from 0 to 100
        self.high_PWM = 100  # On a scale from 0 to 100
        # For the PWM.
        self.pin = PWMOutputDevice(18)

    # Automatically connect to the VTN instead of prompting the user.
    def _use_this_VTN(self, name, info):
        # Wait two seconds, because this behaves poorly if the server is just spinning up.
        time.sleep(2)
        return True

    # If there are no programs on the VTN, wait for 4 seconds and scan again.
    def _no_programs_try_again(self):
        self.logger.info("No programs found. Trying again...")
        time.sleep(4)
        return True

    # Given a list of available programs, simply select the first one.
    def _get_desired_program_index(self, program_list):
        return 0

    def _process_event_interval(self, interval):
        interval_id = interval.get('id', 0)
        self.interval_id = interval_id
        payload = interval.get('payloads', [])[0]
        cur_price = payload.get('values', [])[0]
        self.current_price = cur_price
        self.logger.debug(f'operateOnProgramEvents,curPrice={cur_price}')

        # If the price is low, run the PWM high throttle.
        if cur_price <= self.low_price:
            cur_PWM = self.high_PWM
            cur_mode = "Fully On"
        # If the price is too high, turn off the PWM device.
        elif cur_price > self.high_price:
            cur_PWM = 0
            cur_mode = "Off"
        # Otherwise, linearly scale the PWM based on pricing.
        else:
            # I think this is correct..
            cur_PWM = ((self.high_price - cur_price)/(self.high_price - self.low_price))*(self.high_PWM - self.low_PWM) + self.low_PWM
            # If cur_price == self.high_price, then cur_PWM = self.low_PWM.
            # If cur_price == self.low_price, then cur_PWM = self.high_PWM.
            cur_mode = "Reduced Power"
        self.current_mode = cur_mode
        self.current_PWM = cur_PWM

        # Set the PWM appropriately.
        self.pin.value = cur_PWM / 100

        # Display some text appropriately.
        self.logger.info(f'Interval: {interval_id}, Price: {round(cur_price,2)}, Mode: {cur_mode}, PWM: {round(cur_PWM,0)} percent')

    # Operates on the events for our selected program.
    def _operate_on_program_events(self):
        if self.events is None:
            self.logger.info("No events found.")
        elif len(self.events) > 0 and self.events[0]:
            self.logger.debug(f'operateOnProgramEvents,event={pprint.pformat(self.events, indent=2)}')
            #
            event_intervals = self.events[0].getIntervals()
            event_intervals_dict = {item['id']: item for item in event_intervals}
            now_id = get_index_in_variable_interval(self.interval_sleep)
            for i in range(now_id, 24):
                self._process_event_interval(event_intervals_dict.get(i,{}))
                time.sleep(seconds_until_next_step(self.interval_sleep))
        else:
            self.logger.info(f'operateOnProgramEventsNoEvents!')

    # Waits until an appropriate time to grab the next program.
    def _wait(self):
        #time.sleep(self.interval_sleep)
        self.logger.info(f'Pause/wait 0 seconds before fetching next 24 hours of prices')
        return


def create_ven_app(ven, ven_name: str):

    app = Flask(ven_name.upper())

    @app.route("/")
    def home():
        return render_template(f'{ven_name}.html')

    @app.route('/chart_data')
    def data():
        # Get current price data from the event
        current_price = ven.current_price
        throttle = ven.current_PWM / 100
        # Calculate min and max for gauge range
        # Using a buffer of 20% below min and above max for better visualization
        min_price = 0
        max_price = 1
        hour = ven.interval_id

        # Create gauge chart data
        gauge_data = {
            "currentValue": current_price,
            "min": min_price,
            "max": max_price,
            "currentThrottle": throttle,
            "minThrottle": 0,
            "maxThrottle": 1,
            "currentHour": hour,
            # Static threshold values for price gauge
            "priceLowThreshold": ven.low_price,  # Static value for low price threshold
            "priceHighThreshold": ven.high_price,  # Static value for high price threshold
            # Static threshold values for throttle gauge
            "throttleLowThreshold": ven.low_PWM / 100,  # Static value for low throttle threshold
            "throttleHighThreshold": ven.high_PWM / 100  # Static value for high throttle threshold
        }
        return jsonify(gauge_data)

    return app


def serve(app):
    http_server = wsgiserver.WSGIServer(app, host='0.0.0.0', port=8081)
    http_server.start()

if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger('EV-VEN')
    logger.setLevel(logging.INFO)

    a_ven = HVAC_VEN("./configs/ev.json", logger=logger)

    app = create_ven_app(a_ven, 'ev')

    # Run the server in a separate thread
    thread = Thread(target=partial(serve, app))
    thread.daemon = True  # Optional: stop server when main thread exits
    thread.start()

    a_ven.run()
    logger.info("Done.")
