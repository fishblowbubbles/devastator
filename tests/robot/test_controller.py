import argparse
import sys
import numpy as np

sys.path.append("./devastator")

import navigation.controllers as controllers
import navigation.physical_chassis as potato
from robot import romeo
# import robot.romeo as romeo
# from vision.helpers import livestream, split_rgbd
# from vision.tracker import Tracker
# import multiprocessing as mp

chassis_params = {
    'motor_force_constant' : 20, # not measured yet, in Newtons/(drive_unit) where -1 < drive_unit < 1
    'track_width' : 0.19, # in meters 
    'motor_damping_constant' : 40, # not measured yet, in N/(m s^-1)
    'chassis_mass' : 2.6, # not measured yet, in kg
    'chassis_J' : 0.5*2.6*(0.13**2) # moment of inertia, not measured yet
}

model = potato.TrackedChassis(**chassis_params) # see file for constants
controller_params = {
    'debug' : True,
    'A' : model.A,
    'B' : model.B,
    'C' : model.C,
    'D' : model.D,
    'integral_action' : True,
    'gain_method' : 'lqr',
    'Q' : np.matrix([[ 1 , 0 , 0 , 0 , 0 , 0 ],
                     [ 0 , 1 , 0 , 0 , 0 , 0 ],
                     [ 0 , 0 , 10, 0 , 0 , 0 ],
                     [ 0 , 0 , 0 , 1 , 0 , 0 ],
                     [ 0 , 0 , 0 , 0 , 0.000001 , 0 ],
                     [ 0 , 0 , 0 , 0 , 0 , 0.000001 ]
                    ]),
    'R' : 10*np.eye(2),
    'saturation_limits' : np.tile( np.matrix([-1,1]) , (2,1) ),
    'back_calc_weight' : np.matrix([
                                   [ 1 , 0 ],
                                   [ 0 , 1 ]
                                   ]),
    'ports' : {
        'u_man' : 5678, # manual input
        'observation' : 56790, # camera d and theta
        'get_states' : 5680, # not implemented yet!
    },

    'output_host' : romeo.HOST,
    'output_port' : romeo.PORT,

    'output_freq_limit' : 5, # in Hz. 210Hz is good.
    'input_conn_reset_time' : 0.3, # failsafe watchdog on input resets the output to zero if there are no inputs
    'predict_freq_limit' : 220,
}

if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--host", default=realsense.HOST)
    # parser.add_argument("--port", type=int, default=realsense.PORT)
    # args = parser.parse_args()

    # procs = []

    controller = controllers.FullStateFeedbackController(**controller_params)

    controller.run()

    
