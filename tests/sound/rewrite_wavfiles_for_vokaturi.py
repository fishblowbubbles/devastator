
import os
import glob
import numpy as np
import librosa
from scipy.io import wavfile

def main(pathAudio):
    counter = 0
    for wav in glob.glob(os.path.join(pathAudio,'*.wav')):
        #print(wav)
        y, sr = librosa.load(wav, sr = 16000, mono=True)
        y = y * 32767 / max(0.01, np.max(np.abs(y)))
        
        files = [os.path.splitext(filename)[0] for filename in os.listdir(pathAudio)]
        wavfile.write("./Female/Actor02/Happy/" + files[counter] + ".wav", sr, y.astype(np.int16))
        counter+=1

main('C:/Users/Wesley Ee/Desktop/JARVIS/Prototype2/examples/Female/Actor02/Happy/')
