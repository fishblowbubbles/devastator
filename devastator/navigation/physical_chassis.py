'''physical model of the robot'''

import numpy as np
import control

### Physical Parameters of the chassis ###
params = {
    'motor_force_constant' : 20, # not measured yet, in Newtons/(drive_unit) where -1 < drive_unit < 1
    'track_width' : 0.15, # not measured yet, in meters 
    'motor_damping_constant' : 20, # not measured yet, in N/(m s^-1)
    'chassis_mass' : 3, # not measured yet, in kg
    'chassis_J' : 1 # moment of inertia, not measured yet
}

class TrackedChassis(object):
    '''
    Calculates the physical model of a robot chassis 
    driven by 2 dc motors driving 2 tracks
    '''
    def __init__(self, params):
        # using dict.get(key, default) to set defaults 
        self.b = params.get('motor_damping_constant', 1)
        self.k_motor = params.get('motor_force_constant', 1)
        self.m = params.get('chassis_mass', 1)
        self.width = params.get('track_width', 1)
        
        # calculate dynamics
        # x_dot = Ax + Bu
        # y     = Cx + Du
        b = self.b
        m = self.m

        # A matrix
        self.A = np.matrix([
            [  0  ,  1  ,  0  ,  0  ],
            [  0  ,-b/m ,  0  ,  0  ],
            [  0  ,  0  ,  0  ,  1  ],
            [  0  ,  0  ,  0  ,-b/m ]
        ])

        # B matrix
        k = self.k_motor
        r = self.width/2.0
        self.B = np.matrix([
            [  0  ,  0  ],
            [  k  ,  0  ],
            [  0  ,  0  ],
            [  0  , k*r ]
        ])

        # C matrix
        self.C = np.matrix([
            [  1  ,  0  ,  0  ,  0  ],
            [  0  ,  0  ,  1  ,  0  ]
        ])

        # D matrix
        # D = 0
        self.D = np.zeros((self.C.shape[0], self.B.shape[1]))

        # reality check on feasibility of system
        assert np.linalg.det(control.ctrb(self.A, self.B)) is not 0, "System is not controllable!"

        #construct a continuous time system
        self.sys_ct = control.ss(self.A, self.B, self.C, self.D)

    def get_sys_dt(self, dt):
        return control.sample_system(self.sys_ct, dt)






