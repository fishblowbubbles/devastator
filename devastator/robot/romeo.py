import serial
from pathlib import Path as p
from time import sleep

"""
Refer to /arduino/romeo/romeo.ino for the code that this python library interfaces.
The arduino code runs on a DFRobot Romeo v2.0
"""

## Global vars
romeo = p('/dev/ttyACM0')

## TODO
## need to fix the reconnection issue when resetting romeo


## TODO
## add some ping functionality so if python crashes the bot will stop
## maybe use some special ASCII character?

## TODO
## fix the motor cutout at low PWM. use a HPF to bump the motor out of friction.
## implement this in the romeo.
## also i think the cutout pwm is a bit too low. maybe 11% is good?


class Devastator(object):
    def __init__(self, device_path='/dev/ttyACM0', timeout=1):
        self.baudrate = 115200
        self.path = device_path
        self.ser = serial.Serial(self.path, self.baudrate)
        self.reverse = {1: True, 2: False}
        self.timeout = timeout
        self.enable()

    def set_direction(self, reverse_m1=False, reverse_m2=False):
        """
        A fix for the direction coz martin is lazy to swap the motor polarity.
        """
        pass
    
    def trim(self, motor, direction, volt_delta = 0.05):
        """
        Trim the motor speeds so that a zero turning command will result in a nominally straight path for the robot.
        """
        pass
    
    def set_controller_verbosity(self, verbosity):
        """ 
        For debugging purposes, enables debug output over serial.
        """
        pass
    
    def set_overshoot(magnitude, length):
        """
        Sets the overshoot magnitude and length of the high shelf filter in the motor controller 
        to tune the aggressiveness of the controller during a step change of motor power.
        """
        pass

    def set_motor_gamma(self, gamma):
        """
        Sets the nonlinearity of the motor response.

        PWM is calculated by the formula (in C language):
        s = m_speed == 0 ? 0 : (pow(abs(m_speed), motor_gamma)*(max_pwm_scale_1 - motor_cut_in_1) + motor_cut_in_1)
        """
        pass

    def set_timeout(self, millis=300):
        """
        NOT IMPLEMENTED IN ARDUINO CODE YET
        
        Used to set the timeout for the watchdog timer in the arduino to stop running the motors in case python stops working.
        """
        pass
        
    def _send(self, msg):
        '''wraps the message in the correct format'''
        self.ser.write((msg + '\n').encode('utf-8'))
        # return self.ser.read_until().decode('utf-8')[:-2]

    def enable(self):
        '''enables the motors'''
        self._send('enable')
        self.buzz([1, 3])

    def buzz(self, pattern=[1]):
        for i in pattern:
            self.__call__(1, 0.01)
            sleep(0.04 * i)
            self.__call__(1, 0)
            sleep(0.05)

    def disable(self):
        '''disables the motors and rejects any further commands'''
        self._send('disable')

    def test(self):
        '''runs a min to max motor speed sweep'''
        self._send('test')

    def lol(self, n_times=1):
        '''partay time'''
        self._send('lol ' + str(n_times))

    def set_motor_speed(self, motor, speed):
        '''sets the motor speed'''
        self._send('{0} {1:.3f}'.format(int(motor), float(speed)))

    def __call__(self, forward_speed, turn_speed):
        """
        Set the forward speed and turn speed.
        Positive forward_speed will drive the robot forward.
        Positive turn_speed is a left turn.

        note that each command will be clipped to be between -1 and 1 in the romeo.
        """
        s1 = forward_speed - turn_speed
        s2 = forward_speed + turn speed
        self.set_motor_speed(1, s1)
        self.set_motor_speed(2, s2)

if __name__ == "__main__":
    print("Running test on ROMEO motor controller...")
    print("Please make sure robot will not drive off any elevated surface!")
    print("")
    input("Press ENTER to continue test or ^C to abort.")
    import time
    tank = Devastator()
    tank.buzz([1, 1, 1, 1, 1, 1])
    tank.buzz([10, 10, 10, 15])
    for i in range(3):
        tank(1, -1)
        tank(2, -1)
        time.sleep(0.5)
        tank(1, 1)
        tank(2, -1)
        time.sleep(0.5)
        tank(1, -1)
        tank(2, 1)
        time.sleep(0.5)
        tank(1, -1)
        tank(2, -1)
        time.sleep(0.5)
        tank(1, 1)
        tank(2, 1)
        time.sleep(0.5)
    tank.lol(5)
    time.sleep(3)
    tank.test()
    tank.test()
    tank.disable()
    tank.test()
