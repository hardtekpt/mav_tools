#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import sys

import rospy
from mavros_msgs.srv import SetMode, CommandBool, CommandTOL
from mavros_msgs.msg import State
from sensor_msgs.msg import BatteryState

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, Label
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive

from threading import Timer

class set_default_variant_timer():
    def __init__(self, button, duration):
        self.button = button
        self.timer = Timer(duration,self.change_variant,args=[button])
        self.timer.start()
    def change_variant(self,button):
        button.variant = "default"

def handle_button_click(resp, event, mode):

    if mode:
        if resp.mode_sent:
            event.button.variant = "success"
        else:
            event.button.variant = "error"
    else:
        if resp.success:
            event.button.variant = "success"
        else:
            event.button.variant = "error"
    
    set_default_variant_timer(event.button, 1.5)

def state_callback(state_msg:State):

    global state 
    state = state_msg

def battery_callback(battery_msg:BatteryState):

    global battery_state
    battery_state = battery_msg

class CurrentBatteryState(Static):
    
    battery = reactive("battery")

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.set_interval(1 / 60, self.update_battery)

    def update_battery(self) -> None:
        """Method to update the time to the current time."""
        try:
            voltage = battery_state.voltage
            current = battery_state.current
            charge = battery_state.charge
            percentage = battery_state.percentage
            self.battery = (f"Voltage: {voltage:02,.02f}, Current: {current:02,.02f}, Charge: {charge:02,.02f}, Percentage: {percentage:02,.02f}")
        except:
            self.battery = ("Undefined")

    def watch_battery(self, battery: float) -> None:
        """Called when the mode attribute changes."""
        self.update(battery)

class CurrentFlightMode(Static):

    mode = reactive("mode")

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.set_interval(1 / 60, self.update_mode)

    def update_mode(self) -> None:
        """Method to update the time to the current time."""
        try:
            self.mode = state.mode
        except:
            self.mode = "Undefined"

    def watch_mode(self, mode: float) -> None:
        """Called when the mode attribute changes."""
        self.update(mode)

class CurrentArmingState(Static):
    
    mode = reactive("mode")

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.set_interval(1 / 60, self.update_mode)

    def update_mode(self) -> None:
        """Method to update the time to the current time."""
        try:
            if state.armed == True:
                self.mode = "Armed"
            else:
                self.mode = "Disarmed"
        except:
            self.mode = "Undefined"

    def watch_mode(self, mode: float) -> None:
        """Called when the mode attribute changes."""
        self.update(mode)


class FlightModesTitle(Static):

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("Current Flight Mode: ", classes="flight_modes_label")
            yield CurrentFlightMode("Current Mode")

class FlightModes(Static):

    def on_button_pressed(self, event: Button.Pressed) -> None:

        button_id = event.button.id
        if button_id == "manual":
            resp = set_mode(custom_mode='MANUAL')
        elif button_id == "stabilized":
            resp = set_mode(custom_mode='STABILIZED')
        elif button_id == "offboard":
            resp = set_mode(custom_mode='OFFBOARD')
        elif button_id == "hold":
            resp = set_mode(custom_mode='HOLD')

        handle_button_click(resp, event, True)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("Manual", id="manual", variant="default")
            yield Button("Stabilized", id="stabilized", variant="default")
            yield Button("Offboard", id="offboard", variant="default")
            yield Button("Hold", id="hold", variant="default")

class ArmingState(Static):

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("Current Arming State: ", classes="flight_modes_label")
            yield CurrentArmingState("Current Arming State")

class Arming(Static):
    
    def on_button_pressed(self, event: Button.Pressed) -> None:

        button_id = event.button.id
        
        if button_id == "arm":
            resp = arm_disarm(value=True)
        elif button_id == "disarm":
            resp = arm_disarm(value=False)
        elif button_id == "takeoff":
            resp = takeoff(altitude = 1)
        elif button_id == "land":
            resp = land(altitude = 0)

        handle_button_click(resp, event, False)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("Arm", id="arm", variant="default")
            yield Button("Disarm", id="disarm", variant="default")
            yield Button("Takeoff", id="takeoff", variant="default")
            yield Button("Land", id="land", variant="default")

class Battery(Static):
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("Battery Status: ", classes="flight_modes_label")
            yield CurrentBatteryState("Current Battery State")

class MavToolsApp(App):

    CSS_PATH = "mav_tools.css"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield FlightModesTitle()
        yield FlightModes()
        yield ArmingState()
        yield Arming()
        yield Battery()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":

    ns = ""
    if len(sys.argv) == 2:
        ns = sys.argv[1]

    app = MavToolsApp()

    rospy.init_node('mav_tools')

    rospy.Subscriber(ns+"/mavros/state", State, state_callback)
    rospy.Subscriber(ns+"/mavros/battery", BatteryState, battery_callback)

    set_mode = rospy.ServiceProxy(ns+'/mavros/set_mode', SetMode)
    arm_disarm = rospy.ServiceProxy(ns+'/mavros/cmd/arming', CommandBool)
    takeoff = rospy.ServiceProxy(ns+'/mavros/cmd/takeoff', CommandTOL)
    land = rospy.ServiceProxy(ns+'/mavros/cmd/land', CommandTOL)

    app.run()
