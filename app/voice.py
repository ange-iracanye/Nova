import sounddevice as sd
import speech_recognition as sr
import pyttsx3
import numpy as np
import wave


engine = pyttsx3.init()



def speak(text):

    engine.say(text)

    engine.runAndWait()



def listen():


    duration = 5

    samplerate = 44100


    print("Listening...")


    recording = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="int16"
    )


    sd.wait()



    filename = "voice.wav"



    with wave.open(filename, "wb") as file:

        file.setnchannels(1)

        file.setsampwidth(2)

        file.setframerate(samplerate)

        file.writeframes(
            recording.tobytes()
        )



    recognizer = sr.Recognizer()


    with sr.AudioFile(filename) as source:

        audio = recognizer.record(
            source
        )



    try:

        text = recognizer.recognize_google(
            audio
        )

        return text



    except:

        return ""