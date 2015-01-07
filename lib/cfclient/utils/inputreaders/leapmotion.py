#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     ||          ____  _ __                           
#  +------+      / __ )(_) /_______________ _____  ___ 
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2014 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
#  USA.

"""
Leap Motion reader for controlling the Crazyflie. Note that this reader needs
the Leap Motion SDK to be manually copied. See lib/leapsdk/__init__.py for
more info.

Since the Leap Motion doesn't have the same kind of axes/buttons structure as
other input devices this is faked using the following axis/button mapping:

Axes
----
0: Roll (Positive when rotating right)
1: Pitch (Positive when rotating forward)
2: Yaw (Positive when rotating right)
3: Thrust (the higher the detection, the higher the value)

The axes is passed as raw values (in degrees), it's up to the scaling in the
input map to convert them into usable values for flying.

Buttons
-------
0: 0 when five fingers are detected and 1 when less then fingers is detected

"""

__author__ = 'Bitcraze AB'
__all__ = ['LeapmotionReader']

try:
    import leapsdk.Leap as Leap
    from leapsdk.Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture
except Exception as e:
    raise Exception("Leap Motion library probably not installed ({})".format(e))

import logging
import time

logger = logging.getLogger(__name__)

MODULE_MAIN = "LeapmotionReader"
MODULE_NAME = "Leap Motion"

class LeapListener(Leap.Listener):

    def set_data_callback(self, callback):
        self._dcb = callback
        self._nbr_of_fingers = 0

    def on_init(self, controller):
        logger.info("Initialized")

    def on_connect(self, controller):
        logger.info("Connected")

    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        logger.info("Disconnected")

    def on_exit(self, controller):
        logger.info("Exited")

    def nbr_of_fingers(self):
        return self._nbr_of_fingers

    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()

        #logger.info("Frame id: %d, timestamp: %d, hands: %d, fingers: %d, tools: %d, gestures: %d" % (
        #                              frame.id, frame.timestamp, len(frame.hands), len(frame.fingers), len(frame.tools), len(frame.gestures())))
        if not frame.hands.is_empty:
            # Get the first hand
            hand = frame.hands[0]

            normal = hand.palm_normal
            direction = hand.direction
            # Pich and roll are mixed up...

            #roll = -direction.pitch * Leap.RAD_TO_DEG / 30.0
            #pitch = -normal.roll * Leap.RAD_TO_DEG / 30.0
            #yaw = direction.yaw * Leap.RAD_TO_DEG / 70.0
            #thrust = (hand.palm_position[1] - 80)/150.0 # Use the elevation of the hand for thrust

            roll = -direction.pitch * Leap.RAD_TO_DEG
            pitch = -normal.roll * Leap.RAD_TO_DEG
            yaw = direction.yaw * Leap.RAD_TO_DEG
            thrust = hand.palm_position[1]

            axes = [roll, pitch, yaw, thrust]
            buttons = [0]

            #if thrust < 0.0:
            #    thrust = 0.0
            #if thrust > 1.0:
            #    thrust = 1.0

            # Protect against accidental readings. When tilting the had
            # fingers are sometimes lost so only use 4.
            if len(hand.fingers) < 4:
                self._dcb([0.0, 0.0, 0.0, 0.0], [0])
            else:
                self._dcb(axes, buttons)

        else:
            self._dcb([0.0, 0.0, 0.0, 0.0], [0])

class LeapmotionReader():
    """Used for reading data from input devices using the PyGame API."""
    def __init__(self):
        #pygame.init()
        self._ts = 0
        logger.info("Initializing")
        self._listener = LeapListener()
        self._listener.set_data_callback(self.leap_callback)
        logger.info("Created listender")
        self._controller = Leap.Controller()
        logger.info("Created controller")
        self._controller.add_listener(self._listener)
        logger.info("Registered listener")
        self.name = MODULE_NAME

        self._axes = None
        self._buttons = None

    def open(self, deviceId):
        """Initalize the reading and open the device with deviceId and set the mapping for axis/buttons using the
        inputMap"""
        self._axes = [0.0, 0.0, 0.0, 0.0]
        self._buttons = [0]

    def leap_callback(self, axes, buttons):
        #logger.info("AX: {}".format(axes))
        #logger.info("BT: {}".format(buttons))

        self._axes = axes
        self._buttons = buttons

    def read(self):
        """Read input from the selected device."""
        # We only want the pitch/roll cal to be "oneshot", don't
        # save this value.
        #self.data["pitchcal"] = 0.0
        #self.data["rollcal"] = 0.0
        #self.data["estop"] = False

        #if (self._listener.nbr_of_fingers() < 5 and self._listener.nbr_of_fingers() > 3 and (time.time() - self._ts) > 1):
        #    self.data["estop"] = True
        #    self._ts = time.time()
        #    logger.info("Change!!")
        #else:
        #    self.data["estop"] = False

        return [self._axes, self._buttons]

    def devices(self):
        """List all the available devices."""
        dev = []

        # According to API doc only 0 or 1 devices is supported
        logger.info("Devs: {}".format(self._controller.is_connected))
        if self._controller.is_connected:
            dev.append({"id": 0, "name": "Leapmotion"})
        
        return dev

