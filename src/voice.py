import sounddevice as sd
import numpy as np
import pyttsx3
import requests

# Function to listen to microphone and capture audio
def listen_to_microphone(duration=5, fs=44100):
    print("Listening...")
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float64')
    sd.wait()  # Wait until recording is finished
    print("Finished listening.")
    return audio_data

# Function to transcribe audio using Groq's Whisper API
def transcribe_audio(audio_data):
    print("Transcribing audio...")
    audio_bytes = audio_data.tobytes()
    response = requests.post('https://api.groq.com/whisper', files={'file': ('audio.wav', audio_bytes)}, headers={'Authorization': 'Bearer YOUR_API_KEY'})
    transcription = response.json().get('text', 'Transcription failed')
    print("Transcription complete.")
    return transcription

# Function to convert text to speech
def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    print("Spoken text:", text)