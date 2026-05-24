#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import struct
import time
from Rosmaster_Lib import Rosmaster

# ---------------- Constant Definitions ----------------
JS_DEV = "/dev/input/js0"
EVENT_SIZE = struct.calcsize("IhBB")
# Button mappings
BTN_BEEP = 11      # Buzzer button
BTN_MODE = 9       # Enable/disable control mode
BTN_RESET = 7      # Servo reset
BTN_LINEAR = 13    # Linear velocity control button
BTN_ANGLER = 14    # Angular velocity control button

# Joystick/d-pad mappings
AXIS_LX = 0        # Left joystick left/right -> lateral movement
AXIS_LY = 1        # Left joystick up/down -> forward/backward
AXIS_RX = 2        # Right joystick left/right -> rotation
AXIS_HAT_X = 6     # D-pad left/right -> gimbal horizontal
AXIS_HAT_Y = 7     # D-pad up/down -> gimbal pitch

# Joystick normalization range
AXIS_MAX = 32767.0
DEADZONE = 0.05    # Deadzone ratio (5%)
SERVO_STEP = 3     # Servo adjustment angle per step
SERVO_MIN, SERVO_MAX = 0, 180

# ---------------- Car Initialization ----------------
car = Rosmaster(car_type=10, com="/dev/myserial")  # Note: serial device
car.create_receive_threading()

# Gimbal initial angles
servo_x , servo_y = int(os.environ.get("INIT_SERVO_S1")), int(os.environ.get("INIT_SERVO_S2"))
servo_init_x = servo_x
servo_init_y = servo_y
car.set_pwm_servo(2, servo_x)
car.set_pwm_servo(3, servo_y)


# Status
joy_active = False
buzzer_on = False
linear_gear  = 1.0    # Linear velocity multiplier
angular_gear = 1.0    # Angular velocity multiplier

# Current joystick values
axis_state = {
    AXIS_LX: 0.0,
    AXIS_LY: 0.0,
    AXIS_RX: 0.0
}


# ---------------- Utility Functions ----------------
def normalize(val: int) -> float:
    """Normalize joystick input from [-32767,32767] to [-1,1] and apply deadzone"""
    fval = val / AXIS_MAX
    return 0.0 if abs(fval) < DEADZONE else fval

def clamp(val, vmin, vmax):
    return max(vmin, min(vmax, val))

# ---------------- Event Handlers ----------------
def handle_button(number, value):
    """Handle button events"""
    global joy_active, buzzer_on, servo_x, servo_y,linear_gear, angular_gear

    if number == BTN_MODE and value:  # Toggle mode
        joy_active = not joy_active
        print("Joystick Mode:", "Enabled" if joy_active else "Disabled")

    elif number == BTN_BEEP and value:  # Buzzer toggle
        buzzer_on = not buzzer_on
        car.set_beep(1 if buzzer_on else 0)

    elif number == BTN_RESET and value:  # Servo reset
        car.set_pwm_servo(2, servo_init_x)
        car.set_pwm_servo(3, servo_init_y)
        print("Servos reset to center position")

    elif number == BTN_LINEAR and value:  # Linear velocity gear switch
        linear_gear = 1.0 / 5 if linear_gear == 1.0 else 1.0
        print(f"Linear velocity multiplier switched to {linear_gear}")

    elif number == BTN_ANGLER and value:  # Angular velocity gear switch
        angular_gear = 1.0 / 4 if angular_gear == 1.0 else 1.0
        print(f"Angular velocity multiplier switched to {angular_gear}")

def handle_axis(number, value):
    """Handle joystick/d-pad events"""
    global servo_x, servo_y, axis_state

    if not joy_active:
        return

    if number in [AXIS_LX, AXIS_LY, AXIS_RX]:
        if number == AXIS_LX:
            axis_state[AXIS_LX] = -normalize(value) * linear_gear
        elif number == AXIS_LY:
            axis_state[AXIS_LY] = -normalize(value) * linear_gear
        elif number == AXIS_RX:
            axis_state[AXIS_RX] = (-2)*normalize(value) * angular_gear

        # Send all three values after each update
        car.set_car_motion(
            axis_state[AXIS_LY],  # Forward/backward
            axis_state[AXIS_LX],  # Left/right
            axis_state[AXIS_RX]   # Rotation
        )

    elif number == AXIS_HAT_X:  # Gimbal horizontal
        servo_x = clamp(servo_x + int(normalize(value) * SERVO_STEP),
                        SERVO_MIN, SERVO_MAX)
        #print(servo_x)
        car.set_pwm_servo(2, 180 - servo_x)

    elif number == AXIS_HAT_Y:  # Gimbal pitch
        servo_y = clamp(servo_y - int(normalize(value) * SERVO_STEP),
                        SERVO_MIN, 100)
        #print(servo_y)
        car.set_pwm_servo(3, servo_y)

def wait_for_device(path, timeout=30):
    """Wait for joystick device to appear"""
    for i in range(timeout):
        if os.path.exists(path):
            return True
        print(f"Waiting for device {path} ... {i+1}s")
        time.sleep(1)
    return False

# ---------------- Main Loop ----------------
def main():
    try:
        with open(JS_DEV, "rb") as jsdev:
            print("Joystick connected, starting control...")
            while True:
                evbuf = jsdev.read(EVENT_SIZE)
                if not evbuf:
                    continue

                _, value, type_, number = struct.unpack("IhBB", evbuf)

                if type_ & 0x01:      # Button
                    handle_button(number, value)
                elif type_ & 0x02:    # Joystick/d-pad
                    handle_axis(number, value)

    except FileNotFoundError:
        print(f"Joystick device {JS_DEV} not found")
    except KeyboardInterrupt:
        print("\nExiting joystick control")
    finally:
        car.reset_car_state()

# ---------------- Program Entry Point ----------------
if __name__ == "__main__":
    main()
