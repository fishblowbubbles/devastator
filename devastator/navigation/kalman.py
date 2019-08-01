import numpy as np
from scipy.linalg import expm # matrix exponential
import control
from time import time

class KalmanFilter(object):
    '''
    A Kalman filter implementation.

    Adapted from https://github.com/zziz/kalman-filter
    Notation consistent with https://en.wikipedia.org/wiki/Kalman_filter
    '''
    def __init__(self, A=None, B=None, H=None, D=None, Q=None, R=None, P=None, x0=None, **kwds):

        if A is None or H is None:
            raise ValueError("Set proper system dynamics.")
        self.r = 1 if B is None else B.shape[1] # num of inputs
        self.n = 1 if A is None else A.shape[1] # num of states.
        self.m = 1 if H is None else H.shape[0] # num of outputs

        # print(self.r, self.n, self.m)
        
        #H is the state output matrix and also the observation model 

        #all this is in discrete time!!
        self.A = np.zeros((self.n, self.n)) if A is None else A # continuous time state model
        self.B = np.zeros((self.n, self.r)) if B is None else B # continuous time control input model
        self.H = np.zeros((self.m, self.n)) if H is None else H # observation model
        self.D = np.zeros((self.m, self.r)) if D is None else D

        # print("{} shape is {}".format('A', self.A.shape))
        # print("{} shape is {}".format('B', self.B.shape))
        # print("{} shape is {}".format('H', self.H.shape))
        # print("{} shape is {}".format('D', self.D.shape))

        # GO TO statesp.py and comment out the self._remove_useless_states() line.
        self.sysc = control.ss(self.A, self.B, self.H, self.D)
        assert np.array_equal(self.sysc.A, self.A), \
            "IF U SEE THIS ERROR: Comment out the self._remove_useless_states() line in the control library at {}, in statesp.py".format(control.__file__)

        #self.F and self.G will be calculated upon a predict call using update_discrete_model
        
        self.Q = np.eye(self.n) if Q is None else Q # covariance of the process noise
        self.R = np.eye(self.n) if R is None else R # covariance of the observation noise
        self.P = np.eye(self.n) if P is None else P
        self._x = np.zeros((self.n, 1)) if x0 is None else x0 # initialise states

        self.last_time = time()

        # actuator saturation limits 
        # (output of controller and input of mechanical system)
        # rows are the individual elements of u
        # n_cols = 2 always. lower limit then higher limit.
        self.saturation_limits = kwds.get('saturation_limits', 
                                    np.tile(np.array([-1,1]),(self.r, 1))) # default
    
    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        self._x = x

    def saturate_controller_outputs(self, u):
        u_clipped = np.clip(u, self.saturation_limits[:,0], self.saturation_limits[:,1])
        return u_clipped
        
    def update_discrete_model(self, dt):
        '''
        creates the discrete system due to non-constant dt
        '''
        self.sysd = control.sample_system(self.sysc, dt) # create a discrete time model
        self.F = self.sysd.A
        self.G = self.sysd.B

    def get_states(self):
        return self._x

    def predict(self, u=None):
        '''
        Takes in input u and outputs an estimation of the internal state x.
        Prediction is based on system dynamics.
        '''
        current_time = time()
        dt = current_time - self.last_time
        self.last_time = current_time
        u = np.zeros((self.r, 1)) if u is None else self.saturate_controller_outputs(u)
        self.update_discrete_model(dt)
        self._x = np.dot(self.F, self._x) + np.dot(self.G, u)
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q
        return self._x

    def update(self, z):
        '''
        Updates the filter's internal states based on an observation of the system, z.
        '''
        y = z - np.dot(self.H, self._x)
        S = self.R + np.dot(self.H, np.dot(self.P, self.H.T))
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))
        self._x = self._x + np.dot(K, y)
        I = np.eye(self.n)
        self.P = np.dot(
            np.dot(I - np.dot(K, self.H), self.P), (I - np.dot(K, self.H)).T
        ) + np.dot(np.dot(K, self.R), K.T)
        return self._x