'''
Input: distance to target and angle to target
Setpoint: distance to target
Output: motor commands
'''
import asyncio
import sys
import numpy as np
import control
import pickle
import socket

# local imports
import kalman
import physical_chassis as potato
import controllers

## TODO: IMPLEMENT MANUAL CONTROL TRACKING FOR NO AUTO/MANUAL MODE SWITCHING TRANSIENT ##
##       THIS IS DONE BY SETTING THE CLIP POINTS TO THE MANUAL VALUE EXACTLY.          ##

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
    'saturation_limits' : np.tile( np.array([-1,1]) , (2,1) ),
    'back_calc_weight' : np.matrix([
                                   [ 1 , 0 ],
                                   [ 0 , 1 ]
                                   ])
}

def get_romeo_commands():
    '''
    returns commands to be sent to the romeo controller
    '''
    u = controller.get_controller_output()
    T = np.matrix([
        [ 0.5 , 0.5 ],
        [-0.5 ,-0.5 ]
    ])
    romeo_commands = T @ u[0:2,:]
    forward_command = romeo_commands[0:...]
    turn_command = romeo_commands[1,...]
    return forward_command, turn_command

async def handler(conn):
    while True:
        observation = await loop.sock_recv(conn, 1024)
        if not observation:
            break
        try:
            msg = pickle.loads(msg)
            # update states based on new observation of system
            controller.update_states(self, observation) 
        except pickle.UnpicklingError:
            print('Unable to unpickle msg: {}'.format(observation))

        # await loop.sock_sendall(conn, msg)
    conn.close()

async def server():
    while True:
        conn, addr = await loop.sock_accept(s)
        loop.create_task(handler(conn))

if __name__ == "__main__":
    try:
        controller = controllers.FullStateFeedbackController(**controller_params)

        loop = asyncio.get_event_loop()
        s = socket.socket()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setblocking(False)
        s.bind((host, port))
        s.listen(10)
        loop.create_task(server())
        loop.run_forever()
    finally:
        loop.close()







