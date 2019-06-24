
#import sys
import scipy.io.wavfile
import os 

#sys.path.append("../api")
import Vokaturi
import glob
    

def vokaturiFunc(filename, emotion):
    #print ("Loading library...")
    Vokaturi.load("../lib/open/win/OpenVokaturi-3-0-win64.dll")
    #print ("Analyzed by: %s" % Vokaturi.versionAndLicense())

    #print ("Reading sound file...")
    (sample_rate, samples) = scipy.io.wavfile.read(filename)
    #sample_rate, bit, samples = convert(filename)
    #print ("   sample rate %.3f Hz" % sample_rate)

    #print ("Allocating Vokaturi sample array...")
    buffer_length = len(samples)
    #print ("   %d samples, %d channels" % (buffer_length, samples.ndim))
    c_buffer = Vokaturi.SampleArrayC(buffer_length)
    if samples.ndim == 1:  # mono
        c_buffer[:] = samples[:] / 32768.0
    else:  # stereo
        c_buffer[:] = 0.5*(samples[:,0]+0.0+samples[:,1]) / 32768.0

    #print ("Creating VokaturiVoice...")
    voice = Vokaturi.Voice (sample_rate, buffer_length)

    #print ("Filling VokaturiVoice with samples...")
    voice.fill(buffer_length, c_buffer)

    print ("Primary emotion is :")
    quality = Vokaturi.Quality()
    emotionProbabilities = Vokaturi.EmotionProbabilities()
    voice.extract(quality, emotionProbabilities)

    if quality.valid:
    ###  To see emotion values
#        print ("Neutral: %.3f" % emotionProbabilities.neutrality)
#        print ("Happy: %.3f" % emotionProbabilities.happiness)
#        print ("Sad: %.3f" % emotionProbabilities.sadness)
#        print ("Angry: %.3f" % emotionProbabilities.anger)
#        print ("Fear: %.3f" % emotionProbabilities.fear)
        
        Neutrality = emotionProbabilities.neutrality 
        Happiness = emotionProbabilities.happiness
        Sadness = emotionProbabilities.sadness
        Anger = emotionProbabilities.anger
        Fear = emotionProbabilities.fear
        pri_emotion = max(Neutrality,Happiness,Sadness,Anger,Fear)
    
        if Neutrality == pri_emotion:
            pred_emo = 'Neutrality'
        elif Happiness == pri_emotion:
            pred_emo = 'Happiness'
        elif Sadness == pri_emotion:
            pred_emo = 'Sadness' 
        elif Anger == pri_emotion:
            pred_emo = 'Anger'
        elif Fear == pri_emotion:
            pred_emo = 'Fear'
        
        if pred_emo == emotion: 
            correct_preds += 1

    voice.destroy()
    return correct_preds
    
fem_angry_path = "./Female/Angry/"
fem_fear_path = "./Female/Fear/"
fem_happy_path = "./Female/Happy/"
fem_neutral_path = "./Female/Neutral/"
fem_sad_path = "./Female/Sad/"

male_angry_path = "./Male/Angry/"
male_fear_path = "./Male/Fear/"
male_happy_path = "./Male/Happy/"
male_neutral_path = "./Male/Neutral/"
male_sad_path = "./Male/Sad/"

correct_preds = 0

fem_angry_correct = 0
fem_fear_correct = 0 
fem_happy_correct = 0
fem_neutral_correct = 0
fem_sad_correct = 0

male_angry_correct = 0
male_fear_correct = 0
male_happy_correct = 0
male_neutral_correct = 0
male_sad_correct = 0

total_fem_angry = 96
total_fem_fear = 96
total_fem_happy = 96
total_fem_neutral = 48
total_fem_sad = 96

total_fem = 432

total_male_angry = 96
total_male_fear = 96
total_male_happy = 96
total_male_neutral = 48
total_male_sad = 96

total_male = 432

total = 864


for filename in glob.glob(os.path.join(fem_angry_path, '*.wav')):
    vokaturiFunc(filename, 'Anger')
    fem_angry_correct = correct_preds
    fem_anger_accuracy = (fem_angry_correct/total_fem_angry) * 100 
    print(fem_anger_accuracy)
    
for filename in glob.glob(os.path.join(fem_fear_path, '*.wav')):
    vokaturiFunc(filename, 'Fear')
    fem_fear_correct = correct_preds
    fem_fear_accuracy = (fem_fear_correct/total_fem_fear) * 100 
    print(fem_fear_accuracy)
       
for filename in glob.glob(os.path.join(fem_happy_path, '*.wav')):
    vokaturiFunc(filename, 'Happiness')
    fem_happy_correct = correct_preds
    fem_happy_accuracy = (fem_happy_correct/total_fem_happy) * 100 
    print(fem_happy_accuracy)
            
for filename in glob.glob(os.path.join(fem_angry_path, '*.wav')):
    vokaturiFunc(filename, 'Neutrality')
    fem_neutral_correct = correct_preds
    fem_neutral_accuracy = (fem_neutral_correct/total_fem_neutral) * 100 
    print(fem_neutral_accuracy)
       
for filename in glob.glob(os.path.join(fem_sad_path, '*.wav')):
    vokaturiFunc(filename, 'Sadness')
    fem_sad_correct = correct_preds
    fem_sad_accuracy = (fem_sad_correct/total_fem_sad) * 100 
    print(fem_sad_accuracy)
    
total_fem_correct = fem_angry_correct + fem_fear_correct + fem_happy_correct + fem_neutral_correct +  fem_sad_correct
total_fem_acc = (total_fem_correct/total_fem) * 100
print(total_fem_acc)
#################
    
for filename in glob.glob(os.path.join(male_angry_path, '*.wav')):
    vokaturiFunc(filename, 'Anger')
    male_angry_correct = correct_preds
    male_anger_accuracy = (male_angry_correct/total_male_angry) * 100 
    print(male_anger_accuracy)
    
for filename in glob.glob(os.path.join(male_fear_path, '*.wav')):
    vokaturiFunc(filename, 'Fear')
    male_fear_correct = correct_preds
    male_fear_accuracy = (male_fear_correct/total_male_fear) * 100 
    print(male_fear_accuracy)
       
for filename in glob.glob(os.path.join(male_happy_path, '*.wav')):
    vokaturiFunc(filename, 'Happiness')
    male_happy_correct = correct_preds
    male_happy_accuracy = (male_happy_correct/total_male_happy) * 100 
    print(male_happy_accuracy)
            
for filename in glob.glob(os.path.join(male_angry_path, '*.wav')):
    vokaturiFunc(filename, 'Neutrality')
    male_neutral_correct = correct_preds
    male_neutral_accuracy = (male_neutral_correct/total_male_neutral) * 100 
    print(male_neutral_accuracy)
       
for filename in glob.glob(os.path.join(male_sad_path, '*.wav')):
    vokaturiFunc(filename, 'Sadness')
    male_sad_correct = correct_preds
    male_sad_accuracy = (male_sad_correct/total_male_sad) * 100 
    print(male_sad_accuracy)
   
total_male_correct = male_angry_correct + male_fear_correct + male_happy_correct + male_neutral_correct +  male_sad_correct
total_male_acc = (total_male_correct/total_male) * 100
print(total_male_acc)

total_correct = total_fem_correct + total_male_correct
total_acc = (total_correct/total) *100
print(total_acc)