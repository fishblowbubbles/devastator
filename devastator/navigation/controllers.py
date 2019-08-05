import sys
import numpy as np
from control import ss, sample_system, place, acker, lqr
import navigation.kalman as kalman
import asyncio
import pickle
import socket

from concurrent.futures import ThreadPoolExecutor
from time import time, sleep
import warnings

# cheat codes
try:
    import uvloop
except Exception as e:
    print("uvloop not installed! Defaulting to asyncio event loop.\n")
    UVLOOP_EXISTS = False
else:
    UVLOOP_EXISTS = True

# from numba import jit



class FullStateFeedbackController(object):
    '''
    Full state feedback controller
    '''
    def __init__(self, *args, **kwds):
        self.debug = kwds.get('debug', False)
        self.debug_states = kwds.get('debug_states', False)

        self._target = np.matrix([
            [1.0],
            [0.0]
        ])

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

        self.A = A # continuous time state matrix 
        self.B = B # input matrix
        self.C = C # output matrix
        self.D = D # feedforward matrix
        self.n = n # num of states
        self.m = m # num of outputs
        self.r = r # num of inputs

        self.sys_orig = ss(self.A, self.B, self.C, self.D)

        self.integral_action = kwds.get('integral_action', False)
        if self.integral_action is True:
            A_aug, B_aug, C_aug, D_aug, n_aug, m_aug, r_aug = self._augment_sys(A, B, C, D, n, m, r)

            self.A_aug = A_aug # continuous time state matrix 
            self.B_aug = B_aug # input matrix
            self.C_aug = C_aug # output matrix
            self.D_aug = D_aug # feedforward matrix
            self.n = n_aug # num of states
            self.m = m_aug # num of outputs
            self.r = r_aug # num of inputs

            self.sysc = ss(self.A_aug, self.B_aug, self.C_aug, self.D_aug)
        
        else:
            self.sysc = ss(self.A, self.B, self.C, self.D)

        self.poles = kwds.get("poles", None)

        #LQR params
        self.Q = kwds.get("Q", None)
        self.R = kwds.get("R", None)
        self.N = kwds.get("N", None)

        # method of calculating the feedback gain matrix K
        self.gain_method = kwds.get("gain_method", 'lqr')

        if self.N is None:
            LQR_args = (self.sysc.A, self.sysc.B, self.Q, self.R)
        else:
            LQR_args = (self.sysc.A, self.sysc.B, self.Q, self.R, self.N)

        place_args = (self.sysc.A, self.sysc.B, self.poles)

        gm = { # user options for gain methods
            'pp' : (place, place_args), # pole placement, no repeated poles
            'lqr': (self.LQR, LQR_args), # Linear Quadratic Regulator
            'acker': (acker, place_args) # repeated poles allowed
        }

        g = gm.get(self.gain_method, None)
        if g is not None:
            self.K = g[0](*g[1])

            #DEBUG K
            # self.K = np.matrix(self.K) @ np.matrix(np.diag([1,1,0,0,1,0])) #debug distance
            # self.K = np.matrix(self.K) @ np.matrix(np.diag([0,0,1,1,0,1])) #debug angle

            if self.debug is True:
                print('K :\n{}\n'.format(self.K))
        
        if self.integral_action is True:
            self.Ki = -self.K[:,-self.m:]
            self.Kt = np.linalg.pinv(self.Ki)

            if self.debug is True:
                print('Kt :\n{}\n'.format(self.Kt))
                
            self.back_calc_weight = kwds.get("back_calc_weight", np.eye(self.m)) 
            self.Kt = self.back_calc_weight @ self.Kt
            self.r, self.B_aug, self.D_aug = self._augment_BD(self.r, self.sysc.B, self.sysc.D, self.Kt)
            self.sysc = ss(self.sysc.A, self.B_aug, self.sysc.C, self.D_aug)
        
        if self.debug is True:
            print('n : {}'.format(self.n))
            print('m : {}'.format(self.m))
            print('r : {}'.format(self.r))
            print('A :\n{}\n'.format(self.sysc.A))
            print('B :\n{}\n'.format(self.sysc.B))
            print('C :\n{}\n'.format(self.sysc.C))
            print('D :\n{}\n'.format(self.sysc.D))
            print('B_aug :\n{}\n'.format(self.B_aug))
            print('D_aug :\n{}\n'.format(self.D_aug))
            

        # rows for each input.
        # each row specifies the [lower_limit, upper_limit] of saturation. 
        self._auto_saturation_limits = kwds.get("saturation_limits",
                                    np.tile( np.matrix([-1,1]) , (self.r,1) )
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
        
        # kalman_H = kwds.get('observation_model', None)
        # if kalman_H is None:
        #     warnings.warn('No observation model specified. Assuming only the output y of the system can be observed...')
        #     kalman_H = self.sysc.C
        #     kalman_D
        # elif self.debug is True:


        # kalman params
        kalman_kwds = {
            'debug' : True,
            'A' : self.sysc.A,
            'B' : self.sysc.B,
            'H' : self.sysc.C,
            'D' : self.sysc.D,
            'process_covariance' : kwds.get('process_covariance', None),
            'measurement_covariance' : kwds.get('measurement_covariance', None),
            'saturation_limits' : self._saturation_limits,
        }
        self.observer = kalman.KalmanFilter(**kalman_kwds)
        self.prev_u_aug = np.matrix(np.zeros((1, self.r)).reshape((self.r,1)))

        socks = kwds.get('socks', None)
        if socks is None:
            print('Using default sockets.')
            self.socks = {
                'u_man' : socket.socket(),
                'observation' : socket.socket(),
                'get_states' : socket.socket(),
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
        else: self.ports = ports

        hosts = kwds.get('hosts', None)
        if hosts is None:
            self.hosts = {
                'u_man' : 'localhost',
                'observation' : 'localhost',
                'u_out' : 'localhost',
                'get_states' : 'localhost'
            }
        else: self.hosts = hosts

        for name, sock in self.socks.items():
            print('Initialising sockets: {}'.format(name))
            sock.setblocking(False)
            sock.bind((self.hosts.get(name, 'localhost'), self.ports[name]))
            sock.listen()
        
        # asyncio loop constructor
        if UVLOOP_EXISTS:
            uvloop.install() #go check this out!!
        self._loop = asyncio.get_event_loop()
        self._coros = []

        self._u_man = np.zeros((self.r//2, 1))
        self._y = (np.zeros((self.m, 1)), time())

        self.timeout = kwds.get('timeout', 1)
        if self.debug is True:
            print('\nTimeout = {} seconds\n'.format(self.timeout))

        self.lost = True
        
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
        
        self._output_freq_limit = kwds.get('output_freq_limit', None)
        if self._output_freq_limit is None:
            warnings.warn("Output frequency limit was not set. Defaulting to 200Hz. Set using 'output_freq_limit' in **kwds")
            self._output_freq_limit = 200
        elif self.debug is True:
            print("Output frequency limit was set to {}Hz".format(self._output_freq_limit))
        self.output_sleep_time = 1.0/self._output_freq_limit

        self.input_conn_reset_time = kwds.get('input_conn_reset_time', None)
        if self.input_conn_reset_time is None:
            warnings.warn("Input connection watchdog timeout was not set. Defaulting to 0.3 seconds. Set using 'input_conn_reset_time' in **kwds")
            self.input_conn_reset_time = 0.3
        elif self.debug is True:
            print("Input watchdog timeout set to {} seconds.".format(self.input_conn_reset_time))
        
        
        self._predict_freq_limit = kwds.get('predict_freq_limit', None)
        if self._predict_freq_limit is None:
            warnings.warn("Prediction frequency limit was not set. Defaulting to 250Hz. Set using 'predict_freq_limit' in **kwds")
            self._predict_freq_limit = 250
        elif self.debug is True:
            print("Prediction frequency limit was set to {}Hz".format(self._predict_freq_limit))

        
        self.observation_conn_reset_time = kwds.get('observation_conn_reset_time', None)
        if self.observation_conn_reset_time is None:
            warnings.warn("Observation connection watchdog timeout was not set. Defaulting to 0.1 seconds. Set using 'observation_conn_reset_time' in **kwds")
            self.input_conn_reset_time = 0.1
        elif self.debug is True:
            print("Observation watchdog timeout set to {} seconds.".format(self.observation_conn_reset_time))

        self._prev_input_time = time()
        self._prev_observation_time = time()

        self.predict_refresh_rate = kwds.get('predict_refresh_rate', None)
        if self.predict_refresh_rate is None:
            warnings.warn("Observer prediction refresh rate was not set. Defaulting to 300Hz. Set using 'predict_refresh_rate' in **kwds")
            self.predict_refresh_rate = 300
        self.predict_min_time = 1.0/self.predict_refresh_rate

        if self.debug is True:
            print('\n\nCONTROLLER SUCCESSFULLY INITIALISED!\n\n\n')
    
    ### debug ###
    def print_states(self):
        states = [
            ['mode', self._mode],
            ['x', self.x],
            ['y', self.y],
            ['u_out', self.u_out],
            ['u_man', self.u_man],
            ['u_aug', self.prev_u_aug],
        ]
        for state in states:
            print('{}: {}'.format(*state))


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
        if u_man.shape is self._u_man.shape:
            self._u_man = u_man

    @property
    def u(self):
        return self.prev_u_aug[0:2,:]
    @u.setter
    def u(self, u):
        pass
    
    @property
    def u_out(self):
        return self.prev_u_aug[0:self.m,:]
    
    @u_out.setter
    def u_out(self, u_out):
        pass
    
    @property
    def y(self):
        if time() - self._y[1] < self.timeout:
            return self._y[0]
        else:
            return self._target

    @y.setter
    def y(self, y):
        if y is not None:
            self._y = self._target-y, time()
            self.update_states(self._y[0])
            self.lost = False

    
    # @property
    # def z(self):
    #     return self._z
    
    # @z.setter
    # def z(self):
    #     return self._target - self.y
    
    @property
    def output_freq_limit(self):
        return self._output_freq_limit
    
    @output_freq_limit.setter
    def output_freq_limit(self, limit):
        if isinstance(limit, (int, float)):
            self._output_freq_limit = limit
            self.output_sleep_time = 1.0/self._output_freq_limit

    def _augment_sys(self, A, B, C, D, n, m, r):
        A_aug = np.vstack((A,-C))
        A_aug = np.hstack((A_aug, np.zeros((n+m,m))))
        B_aug = np.vstack((B, np.zeros((m,r))))
        C_aug = np.hstack((C, np.zeros((m,m))))
        n += m
        return A_aug, B_aug, C_aug, D, n, m, r

    def _augment_BD(self, r, B, D, Kt):
        '''
        B_aug = 
        [
            [  B  , 0  ]
            [  0  , Kt ]
        ]
        where Kt is the pseudoinverse of the integral gain Ki
        '''
        r_new = r*2
        L = B
        R = np.vstack((np.zeros((B.shape[0]-Kt.shape[0], Kt.shape[1])), Kt))
        B_aug = np.hstack((L,R))
        D_aug = np.hstack((D,np.zeros((D.shape[0], B_aug.shape[1]-D.shape[1]))))
        if self.debug is True:
            print('B_aug :\n{}\n'.format(B_aug))
        return r_new, B_aug, D_aug
    
    ### pole placement methods ###
    def LQR(self, *args):
        K , _ , _ = lqr(*args)
        return K

    ### CONTROLLER OUTPUTS ###
    def calculate_output(self):
        '''
        Control law: u = -Kx
        splits control signal u into the saturated and unsaturated part -> u_aug
        '''
        x = self.observer.predict(self.prev_u_aug)
        # print(self.K)
        u = -self.K @ x

        if time() - self._y[1] > self.timeout:
            u = np.matrix(np.zeros_like(u))
            # self.observer.reset()
            self.observer.update(np.zeros_like(self._target))
            self.lost = True

        if self._mode is 'auto':
            self._saturation_limits = self._auto_saturation_limits
        elif self._mode is 'manual':
            self._saturation_limits = np.matrix(np.tile(self.u_man, (1,2)))
        u_sat = np.clip(u, self._saturation_limits[:,0],self._saturation_limits[:,1])
        # u_sat_auto = np.clip(u, self._auto_saturation_limits[:,0],self._auto_saturation_limits[:,1])
        u_aug = np.vstack((u_sat, u-u_sat))
        self.prev_u_aug = u_aug
        if self.debug_states is True: self.print_states()
        return u_aug
    
    
    async def predict_states(self):
        print('Starting predict_states...')
        while True:
            predict_start_time = time()
            await self._loop.run_in_executor(self.pool, self.calculate_output) # run in pool
            elapsed = time()-predict_start_time 
            additional_wait = self.predict_min_time - elapsed
            if additional_wait > 0:
                await asyncio.sleep(additional_wait)
            else:
                current_rate = 1.0/elapsed
                warnings.warn('Predict refresh rate below target rate. Currently {}Hz.'.format(self.predict_refresh_rate, current_rate) )
    
    ### input sensor readings ###
    def update_states(self, y):
        self.observer.update(y)

    async def arecv_obj(self, connection, addr):
        packets = []
        while True:
            packet = await self._loop.sock_recv(connection, 1024)
            if not packet:
                break
            packets.append(packet)
        try:
            obj = pickle.loads(b"".join(packets))
            if self.debug is True:
                print('Received an object of type {}'.format(type(obj)))
            return obj
        except pickle.UnpicklingError:
            warnings.warn('Object cannot be unpickled. Raw inp: {}'.format(packets))
            return packets
        except EOFError:
            return None
    
    async def arecv_dict(self, conn, addr):
        obj = await self.arecv_obj(conn, addr)
        if isinstance(obj, dict):
            return obj
        else:
            if self.debug is True:
                warnings.warn('Object received is not a dictionary.')
            return {}
                
    # IO handlers
    async def handle_observation(self, conn, addr):
        try:
            obj = await self.arecv_dict(conn, addr)
            '''
            obj = {
                'y' : np.array([
                    [d],
                    [theta]
                ])
            }
            '''
            y = obj.get('y', None)
            print(y)

            if isinstance(y, (np.matrix, np.ndarray)):
                self._prev_observation_time = time() #reset the observation watchdog timer
                print('obs recv: {}'.format(y))
                self.y = np.matrix(y)
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
            obj = await self.arecv_dict(conn, addr)
            '''
            obj = {
                'u_man' : np.array([
                    [u_left],
                    [u_right]
                ]),
                'mode' : 'manual'
            }
            '''
            u_man = obj.get('u_man', None)
            if isinstance(u_man, (np.matrix, np.ndarray)):
                if u_man.shape == self.u_man.shape:
                    self.u_man = np.matrix(u_man)
                    success = True
                    self._prev_input_time = time() #reset the input watchdog timer
                if self.debug is True:
                    print('States updated. u_man = {}'.format(u_man))
            
            mode = obj.get('mode', None)
            if mode in ['manual', 'auto']:
                self._mode = mode
                success = True
                self._prev_input_time = time() #reset the input watchdog timer
                if self.debug is True:
                    print('States updated. mode = {}'.format(mode))

            if u_man is None and mode is None:
                warnings.warn('Nothing was received.')

        finally:
            conn.close()
            if self.debug is True:
                print('Connection closed: {}'.format(addr))
            return success

    async def aconnect_and_send(self, get_data_func, host, port):
        with socket.socket() as s:
            s.setblocking(False)
            if self.debug is True: print('Awaiting output connection: {}, {}'.format(host, port))
            await self._loop.sock_connect(s, (host, port))
            data = get_data_func()
            pkl = pickle.dumps(data)
            if self.debug is True: print('Output connection established.\nSending...\nData: {}'.format(data))
            await self._loop.sock_sendall(s, pkl)
            if self.debug is True: print('Output sent')
            return True

    async def handle_get_request(self, conn, addr):
        '''
        maintains the connection with and replies whoever wants to get the states of the robot.
        '''
        while True:
            pass

    async def input_watchdog(self):
        print_every = 10
        count = 0
        if self.debug is True: print("Starting input watchdog in 3...")
        await asyncio.sleep(1)
        if self.debug is True: print("Starting input watchdog in 2...")
        await asyncio.sleep(1)
        if self.debug is True: print("Starting input watchdog in 1...")
        await asyncio.sleep(1)
        if self.debug is True: print("Input watchdog started.")
        
        while True:
            time_since_last_inp = time() - self._prev_input_time
            if time_since_last_inp > self.input_conn_reset_time:
                self.u_man = np.zeros_like(self.u_man)
                if self.debug is True:
                    if count is 0: print('No input connection! Time since last input = {:.1f}s'.format(time_since_last_inp))
                count = (count + 1) % print_every
            else:
                count = 0
            await asyncio.sleep(0.05) #check at most every 0.05 seconds
    
    async def observation_watchdog(self):
        print_every = 5
        count = 0
        if self.debug is True: print("Starting observation watchdog in 3...")
        await asyncio.sleep(1)
        if self.debug is True: print("Starting observation watchdog in 2...")
        await asyncio.sleep(1)
        if self.debug is True: print("Starting observation watchdog in 1...")
        await asyncio.sleep(1)
        if self.debug is True: print("Observation watchdog started.")
        
        while True:
            time_since = time() - self._prev_observation_time
            if time_since > self.observation_conn_reset_time:
                self._mode = 'manual'
                if self.debug is True:
                    if count is 0: print('No observation connection! Time since last input = {:.1f}s'.format(time_since))
                count = (count + 1) % print_every
            else:
                count = 0
            await asyncio.sleep(0.05) #check at most every 0.05 seconds

    # IO servers
    async def observation_server(self):
        '''
        receives a connection with measurements (d, theta) taken from the camera
        '''
        sockkey = 'observation'
        success_str = 'Opening observation_server connection from'
        handler = self.handle_observation
        if self.debug is True: print('Starting {} server using {} socket'.format(sockkey, self.socks[sockkey]))
        try:
            while True:
                conn, addr = await self._loop.sock_accept(self.socks[sockkey])
                print(conn, addr)
                if self.debug is True:
                    print(success_str + ' {}'.format(addr))
                self._loop.create_task(handler(conn, addr))
        finally:
            self.socks[sockkey].close()
    
    async def manual_control_server(self):
        '''
        takes in manual commands from the app or xbox controller
        '''
        sockkey = 'u_man'
        success_str = 'Opening manual_control_server connection from'
        handler = self.handle_manual_control
        if self.debug is True: print('Starting {} server using {} socket'.format(sockkey, self.socks[sockkey]))
        try:
            while True:
                conn, addr = await self._loop.sock_accept(self.socks[sockkey])
                if self.debug is True:
                    print(success_str + ' {}'.format(addr))
                self._loop.create_task(handler(conn, addr))
        finally:
            self.socks[sockkey].close()
    

    async def output_client(self): 
        '''
        tries to connect to the romeo to give it motor commands
        timeout and sleep before retrying
        '''
        if self.debug is True: print('Starting output client at host={}, port={}'.format(self.output_host, self.output_port))
        
        def get_u_out():

            output = {
                'u_out' : self.u_out
            }

            # output = {
            #     'u_out' : np.matrix([
            #         [1],
            #         [1]
            #     ])
            # }
            return output

        while True:
            # await asyncio.sleep(0.3)
            start_time = time()
            await self.aconnect_and_send(get_u_out, self.output_host, self.output_port)
            time_awaited = time() - start_time
            extra_time = self.output_sleep_time - time_awaited
            if extra_time > 0:
                await asyncio.sleep(extra_time) #limits the output frequency
            else:
                if self.debug is True: warnings.warn('Actual output frequency slower than output_freq_limit')

    async def get_state_server(self): 
        '''
        server to handle random requests to get robot states/properties. no setting of properties are allowed.
        '''
        pass
        
    async def async_tasks(self):
        self.servers = {
            'u_man' : self.manual_control_server,
            'observation' : self.observation_server,
            'u_out' : self.output_client,
            # 'get_state' : self.get_state_server,
        }
        # create tasks
        for name, server in self.servers.items():
            if self.debug is True: print('Starting {} coroutine'.format(name))
            self._coros.append(self._loop.create_task(server()))

        # self._coros.append(self._loop.create_task(self.input_watchdog()))
        # self._coros.append(self._loop.create_task(self.observation_watchdog()))
        self._coros.append(self._loop.create_task(self.predict_states()))

        await asyncio.wait(self._coros)
        return self._coros
    
    def run(self):
        try:
            if self.debug is True: print('Event loop starting ...')
            
            c = self._loop.run_until_complete(self.async_tasks())
            print(c)
        finally:
            if self.debug is True: print('Closing everything ...')
            self.pool.shutdown(wait=True)
            for task in asyncio.Task.all_tasks(self._loop):
                task.cancel()
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.stop()
            self._loop.close()
            if self.debug is True: print('Everything closed.')
            sys.exit(0)
        