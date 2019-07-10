import os
import wave
from pprint import pprint

# import matplotlib.pyplot as plt
import numpy as np
import pyaudio
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage.filters import maximum_filter1d as max_filter
# from tqdm import tqdm


class ReSpeaker(object):
    def __init__(self, with_microphone = True, template_path = 'normalized_template.wav'):
        self.respeaker_rate = 16000
        self.respeaker_channels = 6  # change base on firmwares, default_firmware.bin as 1 or 6_firmware.bin as 6
        self.respeaker_width = 2
        self.chunk = 1024
        self.record_seconds = 5
        self.wav_output_file = "output.wav"
        
        _, self.template = wavfile.read(template_path)

        self.p = pyaudio.PyAudio()
        
        if with_microphone:
            self.respeaker_index = self.get_microphone_index()
            self.stream = self.p.open(
                    rate = self.respeaker_rate,
                    format = self.p.get_format_from_width(self.respeaker_width),
                    channels = self.respeaker_channels,
                    input = True,
                    input_device_index = self.respeaker_index)
            self.data = np.frombuffer(self.stream.read(self.chunk, exception_on_overflow =True), dtype = np.int16)[0::6]

    def get_microphone_index(self):
        info = self.p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = self.p.get_device_info_by_host_api_device_index(0, i)
            if (device_info.get('maxInputChannels')) > 0:
                device_name = device_info.get('name')
                print("Input Device id ", i, " - ", device_name)
                
                if device_name == 'ReSpeaker 4 Mic Array (UAC1.0)':
                    return i
    
    def get_input(self, wav_file = None):
        if wav_file:
            _, self.data = wavfile.read(wav_file)
            if len(self.data.shape) != 1:
                self.data = self.data[:, 0]
            
        else:
            while self.data.shape[0] < 163840:
                inputs = np.frombuffer(self.stream.read(self.chunk, exception_on_overflow =False), dtype = np.int16)[0::6]
                # print(self.data.shape)
                self.data = np.concatenate((self.data, inputs))
    
    @staticmethod
    def normalize(data):
        def rms(d):
            return (sum(d ** 2) / len(d)) ** 0.5
        
        output = data / max(data)
        output = output * rms(output)
        
        return output
    
    def get_correlation(self):
        data = self.normalize(self.data)
        
        correlation = signal.correlate(data, self.template, mode = 'same')
        max_filtered = max_filter(correlation, 2000)
        # thresh = max_filtered > .38
        
        # self.plot(data, max_filtered)
        
        return np.amax(max_filtered) > .5
        
    def plot(self, data, max_filtered):
        plt.clf()
        
        plt.subplot(211)
        plt.plot(data)
        
        plt.subplot(212)
        plt.plot(max_filtered)
        
        plt.show()
        
        truncated_data = self.data[-80000:]
        
        self.data = truncated_data
        
    def record_and_save(self, output_file = None, record_seconds = 0):
        if output_file:
            self.wav_output_file = output_file
        
        if record_seconds:
            self.record_seconds = record_seconds
        
        stream = self.p.open(
                rate = self.respeaker_rate,
                format = self.p.get_format_from_width(self.respeaker_width),
                channels = self.respeaker_channels,
                input = True,
                input_device_index = self.respeaker_index)
        
        print("* recording")
        
        frames = []
        
        for i in range(0, int(self.respeaker_rate / self.chunk * self.record_seconds)):
            data = stream.read(self.chunk)
            # extract channel 0 data from 6 channels, if you want to extract channel 1, please change to [1::6]
            a = np.frombuffer(data, dtype = np.int16)[0::6]
            frames.append(a.tostring())
        
        print("* done recording")
        
        stream.stop_stream()
        stream.close()
        self.p.terminate()
        
        wf = wave.open(self.wav_output_file, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(self.p.get_format_from_width(self.respeaker_width)))
        wf.setframerate(self.respeaker_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
    def walk_and_test(self, root_dir):
        correlation_dict = {}
        
        for root, dirs, files in os.walk(root_dir):
            detection_list = []
            
            # for wav_file in tqdm(files):
            for wav_file in files:
                if '.wav' not in wav_file:
                    continue
                    
                try:
                    self.get_input(os.path.join(root, wav_file))
                    
                    correlation = self.get_correlation()
                    
                    if correlation > .5:
                        gun = 1
                    else:
                        gun = 0
                        
                    correlation_dict[wav_file] = gun
                    detection_list.append(gun)
                
                except ValueError as e:
                    print(os.path.join(root, wav_file))
                    print(e)
                
            if detection_list:
                print(files[0], ': ', sum(detection_list) / len(detection_list))
            
        return correlation_dict
    

if __name__ == '__main__':
    respeaker = ReSpeaker(with_microphone = False, template_path = 'correlation_data/normalized_template.wav')
    respeaker.get_input("correlation_data/Rifle,Bolt Action,.30-06,Arisaka,Gunshot,Processed,3,Medium Distant.wav")
    print(respeaker.get_correlation())
    
    # respeaker.record_and_save(record_seconds = 5)
    # while True:
    #     respeaker.get_input('Processed, Airborne/Handgun, Pistol, Revolver/Handgun,Pistol,Revolver,Double Action,.38 Special,Smith  Wesson 642,Gunshot,Processed,1,Close.wav')
    #     respeaker.get_correlation()
    #     break
    # cordict = respeaker.walk_and_test('Processed, Airborne')
    # cordict = respeaker.walk_and_test('Bang Sounds')
    # print(max(cordict.values()))
    # print(min(cordict.values()))
    # pprint(cordict)
    # print(sum(cordict.values()) / len(cordict))
