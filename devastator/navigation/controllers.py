import numpy as np
from control import ss, sample_system, place, acker, lqr

### TODO ###
# future work:
# implement getters and setters properly

class FullStateFeedbackController(object):
    '''
    Full state feedback controller
    '''
    def __init__(self, *args, **kwds):
        A = kwds.get('A', np.matrix(0))
        B = kwds.get('B', np.matrix(0))
        C = kwds.get('C', np.matrix(0))
        
        n = A.shape[0]
        assert n == A.shape[1], "Matrix A is not square!"
        r = B.shape[1]
        m = C.shape[0]

        D = kwds.get('D', np.zeros((m,r)))

        assert r == D.shape[1], "Num of cols in B and D must be the same."
        assert m == D.shape[0], "Num of rows in C and D must be the same."

        self.integral_action = kwds.get('integral_action', False)
        if self.integral_action is True:
            A, B, C, D, n, m, r = self._augment_sys(A, B, C, D, n, m, r)

        self.A = A # continuous time state matrix 
        self.B = B # input matrix
        self.C = C # output matrix
        self.D = D # feedforward matrix
        self.n = n # num of statesSSS
        self.m = m # num of outputs
        self.r = r # num of inputs

        self.sysc = ss(self.A, self.B, self.C, self.D)

        self.poles = kwds.get("poles", None)

        #LQR params
        self.Q = kwds.get("Q", None)
        self.R = kwds.get("R", None)
        self.N = kwds.get("N", None)

        # method of calculating the feedback gain matrix K
        self.gain_method = kwds.get("gain_method", 'lqr')

        if self.N is None:
            LQR_args = (self.A, self.B, self.Q, self.R)
        else:
            LQR_args = (self.A, self.B, self.Q, self.R, self.N)

        place_args = (self.A, self.B, self.poles)

        gm = { # user options for gain methods
            'pp' : (place, place_args), # pole placement, no repeated poles
            'lqr': (self.LQR, LQR_args), # Linear Quadratic Regulator
            'acker': (acker, place_args) # repeated poles allowed
        }

        g = gm.get(self.gain_method, None)
        if g is not None:
            self.K = g[0](*g[1])
        
        if self.integral_action is True:
            self.Ki = -self.K[:,-self.m:]
            self.Kt = np.linalg.pinv(self.Ki)

            self.back_calc_weight = kwds.get("back_calc_weight", np.eye(self.m)) 
            self.Kt = self.back_calc_weight @ self.Kt
            self.B_aug = self._augment_B(self.B, self.Kt)

        # rows for each input.
        # each row specifies the [lower_limit, upper_limit] of saturation. 
        self.saturation_limits = kwds.get("saturation_limits",
                                    np.tile( np.array([-1,1]) , (self.r,1) )
                                        )   

    def _augment_sys(self, A, B, C, D, n, m, r):
        A_aug = np.vstack((A,-C))
        A_aug = np.hstack((A_aug, np.zeros((n+m,m))))
        B_aug = np.vstack((B, np.zeros((m,r))))
        C_aug = np.hstack((C, np.zeros((m,m))))
        n += m
        return A_aug, B_aug, C_aug, D, n, m, r

    def _augment_B(self, B, Kt):
        '''
        B_aug = 
        [
            [  B  , 0  ]
            [  0  , Kt ]
        ]
        where Kt is the pseudoinverse of the integral gain Ki
        '''
        L = np.vstack((B, np.zeros(self.m,self.r)))
        R = np.vstack((np.zeros((self.n, self.r)), Kt))
        B_aug = np.hstack((L,R))
        return B_aug

    def __call__(self, *args, **kwds):
        '''
        returns the continuous time system if no dt is given.
        returns the discrete time system if dt is given.
        '''
        dt = kwds.get('dt', None)
        if dt is not None:
            return sample_system(self.sysc, dt, method = 'zoh') #discrete time
        return self.sysc
    
    ### pole placement methods ###
    def LQR(self, *args):
        K , _ , _ = lqr(*args)
        return K

    ### CONTROLLER OUTPUTS ###

    def get_controller_output(self, x):
        '''
        Control law: u = -Kx
        splits control signal u into the saturated and unsaturated part -> u_aug
        '''
        u = -self.K @ x
        u_sat = np.clip(
            u, 
            self.saturation_limits[:0],
            self.saturation_limits[:1]
            )
        u_aug = np.vstack((u_sat, u-u_sat))
        return u_aug

if __name__ == "__main__":
    pass