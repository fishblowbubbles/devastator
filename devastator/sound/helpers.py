import os

import scipy.io.wavfile
import speech_recognition as sr

import Vokaturi

r = sr.Recognizer()
counter = 0
filenamelist = []


def writeToWav(audio):
    with open(filenamelist[counter - 1], "wb") as f:
        f.write(audio.get_wav_data())


def listeningFunc(source):
    print("\nListening for 5 seconds :")
    #audio = r.listen(source)   #listen until silence is detected (method 1)
    audio = r.record(
        source, duration=5)  # record 5s of the source (method 2 may be better)
    writeToWav(audio)
    vokaturiFunc(filenamelist[counter - 1])


def vokaturiFunc(filename):
    # print ("Loading library...")
    Vokaturi.load("../lib/open/linux/OpenVokaturi-3-3-linux64.so")
    # print ("Analyzed by: %s" % Vokaturi.versionAndLicense())

    # print ("Reading sound file...")
    (sample_rate, samples) = scipy.io.wavfile.read(filename)
    #print ("   sample rate %.3f Hz" % sample_rate)

    # print ("Allocating Vokaturi sample array...")
    buffer_length = len(samples)
    # print ("   %d samples, %d channels" % (buffer_length, samples.ndim))
    c_buffer = Vokaturi.SampleArrayC(buffer_length)
    if samples.ndim == 1:  # mono
        c_buffer[:] = samples[:] / 32768.0
    else:  # stereo
        c_buffer[:] = 0.5 * (samples[:, 0] + 0.0 + samples[:, 1]) / 32768.0

    # print ("Creating VokaturiVoice...")
    voice = Vokaturi.Voice(sample_rate, buffer_length)

    # print ("Filling VokaturiVoice with samples...")
    voice.fill(buffer_length, c_buffer)

    print("Primary emotion is :")
    quality = Vokaturi.Quality()
    emotionProbabilities = Vokaturi.EmotionProbabilities()
    voice.extract(quality, emotionProbabilities)

    if quality.valid:
        # To see emotion values
        # print ("Neutral: %.3f" % emotionProbabilities.neutrality)
        # print ("Happy: %.3f" % emotionProbabilities.happiness)
        # print ("Sad: %.3f" % emotionProbabilities.sadness)
        # print ("Angry: %.3f" % emotionProbabilities.anger)
        # print ("Fear: %.3f" % emotionProbabilities.fear)

        Neutrality = emotionProbabilities.neutrality
        Happiness = emotionProbabilities.happiness
        Sadness = emotionProbabilities.sadness
        Anger = emotionProbabilities.anger
        Fear = emotionProbabilities.fear
        pri_emotion = max(Neutrality, Happiness, Sadness, Anger, Fear)

        if Neutrality == pri_emotion:
            print('Neutral ->', Neutrality)
        elif Happiness == pri_emotion:
            print('Happy ->', Happiness)
        elif Sadness == pri_emotion:
            print('Sad ->', Sadness)
        elif Anger == pri_emotion:
            print('Angry ->', Anger)
        elif Fear == pri_emotion:
            print('Fearful ->', Fear)

    else:
        print("No voice detected")

    voice.destroy()
    # deletes file after processing to save space
    os.remove(filenamelist[counter -1])


with sr.Microphone() as source:
    while True:
        counter += 1
        # print(counter)
        filename = "testing_wav" + str(counter) + ".wav"
        filenamelist.append(filename)
        # print(filenamelist)
        listeningFunc(source)
