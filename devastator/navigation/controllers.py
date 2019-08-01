import numpy as np
from control import ss, sample_system, place, acker, lqr
import navigation.kalman as kalman
import asyncio
import pickle
import socket
import uvloop
from concurrent.futures import ThreadPoolExecutor
from time import time

### TODO ###
# future work:
# implement getters and setters properly



class FullStateFeedbackController(object):
    '''
    Full state feedback controller
    '''
    def __init__(self, *args, **kwds):
        self.debug = kwds.get('debug', False)
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
        self.n = n # num of states
        self.m = m # num of outputs
        self.r = r # num of inputs

        self.sysc = ss(self.A, self.B, self.C, self.D)

        if self.debug is True:
            print('n : {}'.format(self.n))
            print('m : {}'.format(self.m))
            print('r : {}'.format(self.r))
            print('A :\n{}\n'.format(self.A))
            print('B :\n{}\n'.format(self.B))
            print('C :\n{}\n'.format(self.C))
            print('D :\n{}\n'.format(self.D))

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
            if self.debug is True:
                print('K :\n{}\n'.format(self.K))
        
        if self.integral_action is True:
            self.Ki = -self.K[:,-self.m:]
            self.Kt = np.linalg.pinv(self.Ki)

            if self.debug is True:
                print('Kt :\n{}\n'.format(self.Kt))
                
            self.back_calc_weight = kwds.get("back_calc_weight", np.eye(self.m)) 
            self.Kt = self.back_calc_weight @ self.Kt
            self.B_aug, self.D_aug = self._augment_BD(self.B, self.D, self.Kt)

        # rows for each input.
        # each row specifies the [lower_limit, upper_limit] of saturation. 
        self._auto_saturation_limits = kwds.get("saturation_limits",
                                    np.tile( np.array([-1,1]) , (self.r,1) )
                                        )
        if self.debug is True:
            print('auto_sat_limits :\n{}\n'.format(self._auto_saturation_limits))

        self._mode = kwds.get('mode', 'auto')
        if self._mode is 'auto':
            self._saturation_limits = self._auto_saturation_limits
        elif self._mode is 'manual':
            self._saturation_limits = np.zeros_like(self._auto_saturation_limits)

        self.num_threads = kwds.get('n_threads', 2)
        self.pool = ThreadPoolExecutor(max_workers = self.num_threads)
        
        # kalman params
        kalman_kwds = {
            'A' : self.A,
            'B' : self.B_aug,
            'H' : self.C,
            'D' : self.D_aug,
            'process_covariance' : kwds.get('process_covariance', None),
            'measurement_covariance' : kwds.get('measurement_covariance', None),
            'saturation_limits' : self._saturation_limits
        }
        self.observer = kalman.KalmanFilter(**kalman_kwds)
        self.prev_u_aug = np.zeros((1, self.r*2))

        socks = kwds.get('socks', None)
        if socks is None:
            self.socks = {
                'u_man' : socket.socket(),
                'observation' : socket.socket(),
                'u_out' : socket.socket()
            }
        else:
            self.socks = socks

        ports = kwds.get('ports', None)
        if ports is None:
            self.ports = {
                'u_man' : 5678,
                'observation' : 5679,
                'u_out' : 5680
            }

        for name, sock in self.socks.items():
            sock.setblocking(False)
            sock.bind('localhost', ports[name])
        
        # asyncio loop constructor
        uvloop.install() #go check this out!!
        self._loop = asyncio.get_event_loop()
        self._coros = []

        self._u_man = np.zeros((self.r, 1))
        self._y = None

        self.timeout = kwds.get('timeout', 3.0)
        if self.debug is True:
            print('\nTimeout = {} seconds\n'.format(self.timeout))
        

    ### getters and setters

    @property
    def x(self):
        return self.observer.x
    
    @x.setter
    def x(self, x): # cannot set x from outside
        pass
    
    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        if mode in ['auto', 'manual']:
            self._mode = mode

    @property
    def u_man(self):
        return self._u_man
    
    @u_man.setter
    def u_man(self, u_man):
        if u_man.shape is (self.m,1):
            self._u_man = u_man

    @property
    def u(self):
        if self.mode is 'manual':
            self._u = np.vstack((self.u_man, np.zeros((self.m, 1))))
        elif self.mode is 'auto':
            self._u = self.get_controller_output()
        return self._u

    @u.setter
    def u(self, u):
        pass
    
    @property
    def u_out(self):
        return self.u[0:self.m,:]
    
    @u_out.setter
    def u_out(self, u_out):
        pass
    
    @property
    def y(self):
        if time() - self._y[1] < self.timeout:
            return self._y[0]
        else:
            return None

    @y.setter
    def y(self, y):
        self._y = y, time()
        if y is not None:
            self.update_states(y)

    def _augment_sys(self, A, B, C, D, n, m, r):
        A_aug = np.vstack((A,-C))
        A_aug = np.hstack((A_aug, np.zeros((n+m,m))))
        B_aug = np.vstack((B, np.zeros((m,r))))
        C_aug = np.hstack((C, np.zeros((m,m))))
        n += m
        return A_aug, B_aug, C_aug, D, n, m, r

    def _augment_BD(self, B, D, Kt):
        '''
        B_aug = 
        [
            [  B  , 0  ]
            [  0  , Kt ]
        ]
        where Kt is the pseudoinverse of the integral gain Ki
        '''
        
        L = B
        R = np.vstack((np.zeros((B.shape[0]-Kt.shape[0], Kt.shape[1])), Kt))
        B_aug = np.hstack((L,R))
        D_aug = np.hstack((D,np.zeros((D.shape[0], B_aug.shape[1]-D.shape[1]))))
        if self.debug is True:
            print('B_aug :\n{}\n'.format(B_aug))
        return B_aug, D_aug

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
    def get_controller_output(self):
        '''
        Control law: u = -Kx
        splits control signal u into the saturated and unsaturated part -> u_aug
        '''
        x = self.observer.predict(self.prev_u_aug)
        u = -self.K @ x
        if self.mode is 'auto':
            self._saturation_limits = self._auto_saturation.limits
        elif self.mode is 'manual':
            self._saturation_limits = np.tile(self.u_man, (1,2))
        u_sat = np.clip(
            u, 
            self._saturation_limits[:0],
            self._saturation_limits[:1]
            )
        u_aug = np.vstack((u_sat, u-u_sat))
        self.prev_u_aug = u_aug
        return u_aug
    
    async def predict_states(self):
        while True:
            self.observer.x = await \
                self._loop.run_in_executor(self.pool, self.observer.predict, self.u) # run in pool
            # self.observer.x = self.observer.predict(u = self.u) # run synchronously, which may not be so bad
    
    ### input sensor readings ###
    def update_states(self, y):
        self.observer.update(y)

    # IO handlers
    async def handle_observation(self, conn, addr):
        while True:
            data = await self._loop.sock_recv(conn, 1024)
            if not data:
                break
            else:
                try:
                    unpkl = pickle.loads(data)
                except _pickle.UnpicklingError:
                    print('observation data cannot be unpickled...')
                else:
                    if isinstance(unpkl, dict):
                        y = unpkl.get('y', None)
                        if y is not None:
                            self.y = y
                            if self.debug is True:
                                print('States updated. y = {}'.format(y))
                    else:
                        print('observation data is not a dictionary...')
        if self.debug is True:
            print('Connection closed: {}'.format(addr))
        conn.close()
    
    async def handle_manual_control(self, conn, addr):
        '''
        accepts a pickled dict containing manual inputs and mode commands
        '''
        while True:
            data = await self._loop.sock_recv(conn, 1024)
            if not data:
                break
            else:
                try:
                    unpkl = pickle.loads(data) #should be a dictionary
                except _pickle.UnpicklingError:
                    if self.debug is True:
                        print('Manual control data cannot be unpickled...')
                else:
                    if isinstance(unpkl, dict):
                        if self.debug is True and len(unpkl) is not 0:
                            print('Manual control raw data: {}'.format(y))
                        u_man = unpkl.get('u_man', None)
                        mode = unpkl.get('mode', None)
                        if isinstance(u_man, (np.array, np.matrix)) and u_man.shape == (self.m, 1):
                            self.u_man = u_man
                            if self.debug is True:
                                print('u_man updated: {}'.format(u_man))
                        if mode is in ['manual', 'auto']:
                            self.mode = mode
                            if self.debug is True:
                                print('mode updated: {}'.format(mode))
                    elif self.debug is True:
                        print('Manual control data is not a dictionary...')
        if self.debug is True:
            print('Connection closed: {}'.format(addr))
        conn.close()
    
    async def handle_output(self, conn, addr):
        while True:
            start_time = time()
            msg = pickle.dumps(self.u_man)
            out_args = [conn, msg]
            try:
                await asyncio.wait_for(
                    self._loop.sock_sendall,
                    *out_args,
                    timeout = self.timeout
                )
            except asyncio.TimeoutError:
                if self.debug is True:
                    print("Connection timed out: {}".format(addr))
                break
            sleep_time = (1.0/self.max_update_frequency) - (time()-start_time)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time) #dont update the romeo too fast!!
        if self.debug is True:
            print('Connection closed: {}'.format(addr))
        conn.close()

    async def handle_get_request(self, conn, addr):
        '''
        maintains the connection with and replies whoever wants to get the states of the robot.
        '''
        while True:
            pass

    # IO servers
    async def observation_server(self):
        '''
        receives a connection with measurements (d, theta) taken from the camera
        '''
        while True:
            conn, addr = await self._loop.sock_accept(self.sock)
            if self.debug is True:
                print('Opening observation_server connection: {}'.format(addr))
            self._loop.create_task(self.echo_handler(conn, addr))
    
    async def manual_control_server(self):
        '''takes in manual commands from the app or xbox controller'''
        while True:
            pass
    
    async def output_client(self): 
        '''
        tries to connect to the romeo to give it motor commands
        timeout and sleep before retrying
        '''
        while True:
            pass
    
    async def get_state_server(self): 
        '''
        server to handle random requests to get robot states/properties. no setting of properties are allowed.
        '''
        while True:
            pass
        
    async def async_tasks(self):
        self._coros.append()
        self.servers = {
            'u_man' : self.manual_control_server,
            'observation' : self.observation_server,
            'u_out' : self.output_server
        }
        # create tasks
        for name, server in self.servers.items():
            self._loop.create_server(server, sock = self.socks[name])
    
    def run(self):
        pass

    # async def observation_handler(self, conn):
    #     while True:
    #         observation = await loop.sock_recv(conn, 1024)
    #         if not observation:
    #             break
    #         try:
    #             msg = pickle.loads(msg)
    #             # update states based on new observation of system
    #             self.update_states(observation) 
    #         except pickle.UnpicklingError:
    #             print('Unable to unpickle observations: {} in {}'.format(observation, self.__file__))

    #         # await loop.sock_sendall(conn, msg)
    #     conn.close()

    # async def update_observation_server(self):
    #     while True:
    #         conn, addr = await loop.sock_accept(s)
    #         loop.create_task(observation_handler(conn))
    
    # def run_update_observation_server(self):
    #     try:
    #         loop = asyncio.get_event_loop()
    #         s = socket.socket()
    #         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    #         s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #         s.setblocking(False)
    #         s.bind((host, port))
    #         s.listen(10)
    #         loop.create_task(update_observation_server())
    #         loop.run_forever()
    #     finally:
    #         loop.stop()
    #         loop.close()

if __name__ == "__main__":
    pass