import myfunnybox.audio as audio
import myfunnybox.speech_recognition as speech_recognition

def record_and_recognize(max_duration=None):
    for aud in audio.record_next_voice_input(max_duration):
        cmd = speech_recognition.recognize_voice_command("_all", aud)
        yield cmd