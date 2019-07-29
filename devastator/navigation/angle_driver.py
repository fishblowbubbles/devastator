'''
Input: distance to target and angle to target
Setpoint: distance to target
Output: motor commands
'''
import sys
import numpy as np
import control

# local imports
import kalman
import physical_chassis as potato
import controllers


chassis_params = {
    'motor_force_constant' : 20, # not measured yet, in Newtons/(drive_unit) where -1 < drive_unit < 1
    'track_width' : 0.15, # not measured yet, in meters 
    'motor_damping_constant' : 20, # not measured yet, in N/(m s^-1)
    'chassis_mass' : 3, # not measured yet, in kg
    'chassis_J' : 1 # moment of inertia, not measured yet
}

model = potato.TrackedChassis(**chassis_params) # see file for constants

controller_params = {
    'A' : model.A,
    'B' : model.B,
    'C' : model.C,
    'D' : model.D,
    'integral_action' : True,
    'gain_method' : 'lqr',
    'Q' : np.matrix([[ 1 , 0 , 0 , 0 ],
                     [ 0 , 1 , 0 , 0 ],
                     [ 0 , 0 , 10, 0 ],
                     [ 0 , 0 , 0 , 1 ]
                    ]),
    'R' : 10*np.eye(2),
    'saturation_limits' : np.tile( np.array([-1,1]) , (2,1) ),
    'back_calc_weight' : np.matrix([[ 1 , 0 ],
                                   [ 0 , 1 ]
                                 ])
}

controller = controllers.FullStateFeedbackController(**controller_params)




