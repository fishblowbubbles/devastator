import sys
from importlib import import_module
sys.path.append('./../')

import numpy as np
from control import ss, sample_system, place, acker, lqr
import navigation.kalman as kalman
# kalman = import_module('.', package='kalman')
# from devastator.navigation import kalman
import asyncio
import pickle
import socket

from concurrent.futures import ThreadPoolExecutor
from time import time
import robot.helpers as helpers
# helpers = import_module('.', package = 'robot.helpers')
import warnings

# cheat codes
try:
    import uvloop
except ModuleNotFoundError:
    warnings.warn('u suck coz u dont have uvloop')
    UVLOOP_EXISTS = False
else:
    UVLOOP_EXISTS = True

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

        self.num_threads = kwds.get('n_threads', 3)
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
                'get_states' : socket.socket()
            }
        else:
            self.socks = socks

        ports = kwds.get('ports', None)
        if ports is None:
            self.ports = {
                'u_man' : 5678,
                'observation' : 5679,
                'get_states' : 5680
            }

        hosts = kwds.get('hosts', None)
        if hosts is None:
            self.hosts = {
                'u_man' : 'localhost',
                'observation' : 'localhost',
                'u_out' : 'localhost',
                'get_states' : 'localhost'
            }

        self._listen = {
                'u_man' : 'localhost',
                'observation' : 'localhost',
                'get_states' : 'localhost'
            }

        for name, sock in self.socks.items():
            sock.setblocking(False)
            sock.bind('localhost', ports[name])
        
        # asyncio loop constructor
        if UVLOOP_EXISTS:
            uvloop.install() #go check this out!!
        self._loop = asyncio.get_event_loop()
        self._coros = []

        self._u_man = np.zeros((self.r, 1))
        self._y = None

        self.timeout = kwds.get('timeout', 3.0)
        if self.debug is True:
            print('\nTimeout = {} seconds\n'.format(self.timeout))
        
        self.output_host = kwds.get('output_host', None)
        self.output_port = kwds.get('output_port', None)
        if self.output_host is None:
            self.output_host = 'localhost'
            warnings.warn('No output host specified, using localhost')
        if self.output_port is None:
            if self.debug is True:
                raise KeyError("Specify 'output_port' in __init__ keywords!")
            self.output_port = 12345
            warnings.warn('No output host port specified, using port 12345.')

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

    async def arecv_obj(self, connection, addr):
        packets = []
        while True:
            packet = await self._loop.sock_recv(connnection, 1024)
            if not packet:
                break
            packets.append(packet)
        try:
            obj = pickle.loads(b"".join(packets))
            if self.debug is True:
                print('Received an object of type {}'.format(type(obj)))
            return obj
        except _pickle.UnpicklingError:
            warnings.warn('Object cannot be unpickled.')
            return packets
                
    # IO handlers
    async def handle_observation(self, conn, addr):
        try:
            obj = await arecv_obj(conn)
            assert isinstance(obj, dict), 'Object received is not a dictionary.'

            y = obj.get('y', None)

            if y is not None:
                self.y = y
                if self.debug is True:
                    print('States updated. y = {}'.format(y))
            else:
                warnings.warn("observation key 'y' not received.")
        finally:
            conn.close()
            if self.debug is True:
                print('Connection closed: {}'.format(addr))

    async def handle_manual_control(self, conn, addr):
        '''
        accepts a pickled dict containing manual inputs and mode commands
        '''
        success = False
        try:
            obj = await arecv_obj(conn, addr)
            assert isinstance(obj, dict), 'Object received is not a dictionary.'

            u_man = obj.get('u_man', None)
            if u_man is not None:
                assert isinstance(u_man, (np.array, np.matrix))
                self.u_man = u_man
                success = True
                if self.debug is True:
                    print('States updated. u_man = {}'.format(u_man))
            
            mode = obj.get('mode', None)
            if mode is not None:
                assert mode is 'manual' or mode is 'auto'
                self.mode = mode
                success = True
                if self.debug is True:
                    print('States updated. mode = {}'.format(mode))

            if u_man is None and mode is None:
                warnings.warn('Nothing was received.')

        finally:
            conn.close()
            if self.debug is True:
                print('Connection closed: {}'.format(addr))
            return success

    async def send_output(self, host, port):
        client_args = [host, port]
        success = await self._loop.run_in_executor(self.pool, helpers.connect_and_send, *client_args)
        if success is False:
            warnings.warn('output not sent successfully.')

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
        sockkey = 'y'
        success_str = 'Opening observation_server connection from'
        try:
            while True:
                conn, addr = await self._loop.sock_accept(self.socks[sockkey])
                if self.debug is True:
                    print(success_str + ' {}'.format(addr))
                self._loop.create_task(self.echo_handler(conn, addr))
        finally:
            self.socks[sockkey].close()
    
    async def manual_control_server(self):
        '''
        takes in manual commands from the app or xbox controller
        '''
        sockkey = 'y'
        success_str = 'Opening manual_control_server connection from'
        try:
            while True:
                conn, addr = await self._loop.sock_accept(self.socks[sockkey])
                if self.debug is True:
                    print(success_str + ' {}'.format(addr))
                self._loop.create_task(self.echo_handler(conn, addr))
        finally:
            self.socks[sockkey].close()
    
    async def output_client(self): 
        '''
        tries to connect to the romeo to give it motor commands
        timeout and sleep before retrying
        '''
        while True:
            await send_output(self.output_host, self.output_port)
    
    async def get_state_server(self): 
        '''
        server to handle random requests to get robot states/properties. no setting of properties are allowed.
        '''
        while True:
            pass
        
    async def async_tasks(self):
        self.servers = {
            'u_man' : self.manual_control_server,
            'observation' : self.observation_server,
            'u_out' : self.output_server,
            'get_state' : self.get_state_server
        }
        # create tasks
        for name, server in self.servers.items():
            self._coros.append(server())
    
    def run(self):
        try:
            c = self._loop.run_until_complete(self.async_tasks())
            print(c)
        finally:
            self._pool.shutdown(wait=True)
            for task in asyncio.Task.all_tasks(self._loop):
                task.cancel()
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.stop()
            self._loop.close()
            sys.exit(0)
        