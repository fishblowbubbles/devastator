'''physical model of the robot'''

import numpy as np
import control



class TrackedChassis(object):
    '''
    Calculates the physical model of a robot chassis 
    driven by 2 dc motors driving 2 tracks
    '''
    def __init__(self,*args, **params):
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
        w = self.width

        # A matrix
        self.A = np.matrix([
            [  0  ,  1  ,  0  ,  0   ],
            [  0  ,-b/m ,  0  ,  0   ],
            [  0  ,  0  ,  0  ,  1   ],
            [  0  ,  0  ,  0  ,-b*w/m]
        ])

        # B matrix
        kdm = self.k_motor/m
        r = self.width/2.0
        self.B = np.matrix([
            [   0   ,   0   ],
            [  kdm  ,  kdm  ],
            [   0   ,   0   ],
            [ kdm*r ,-kdm*r ]
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
        self.ctrb = control.ctrb(self.A, self.B)
        assert int(np.linalg.matrix_rank(self.ctrb)) == int(self.ctrb.shape[0]), "System is not controllable!"

        #construct a continuous time system
        self.sys_ct = control.ss(self.A, self.B, self.C, self.D)

    def get_sys_dt(self, dt):
        return control.sample_system(self.sys_ct, dt)






