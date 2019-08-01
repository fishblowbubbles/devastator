import argparse
import sys

sys.path.append("./devastator")

import navigation.controllers as controllers
import robot.romeo as romeo
from vision.helpers import livestream, split_rgbd
from vision.tracker import Tracker
import multiprocessing as mp

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=realsense.HOST)
    parser.add_argument("--port", type=int, default=realsense.PORT)
    args = parser.parse_args()

    procs = []

    controller = controllers.FullStateFeedbackController(**controller_params)

    procs.append(mp.Process(controller)

    for proc in procs():
        procs.run

    
