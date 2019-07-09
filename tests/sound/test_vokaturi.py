import sys

sys.path.append(".")

import speech_recognition as sr

from devastator.sound import Vokaturi
from devastator.sound.helpers import listening_func

if __name__ == "__main__":
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        while True:
            listeningFunc(source)
