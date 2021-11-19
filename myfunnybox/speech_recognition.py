import os
import functools
import json
# from pocketsphinx import LiveSpeech, get_model_path
# from pocketsphinx.pocketsphinx import *
# from sphinxbase.sphinxbase import *

from myfunnybox import MODELS_DIR
import myfunnybox.audio as audio

import vosk

VOICE_COMMANDS = {
    "main": ["coucou", "lecture", "lis moi"],
    "option": ["fois"],
    "num": ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
}
VOICE_COMMANDS["_all"] = sum((v for v in VOICE_COMMANDS.values()), [])

MODEL = "vosk-model-small-fr-pguyot-0.3"

@functools.lru_cache()
def init_model(model):
    return vosk.Model(os.path.join(MODELS_DIR, model))

@functools.lru_cache()
def init_recognizer(voice_commands_key):
    kws = list(set(
        w
        for k in VOICE_COMMANDS[voice_commands_key]
        for w in k.split()
    ))
    model = init_model(MODEL)
    return vosk.KaldiRecognizer(model, audio.RATE, f'["{" ".join(kws)}", "[unk]"]')

def recognize_voice_command(voice_commands_key, aud):
    rec = init_recognizer(voice_commands_key)
    rec.AcceptWaveform(audio.np_to_raw(aud))
    return json.loads(rec.FinalResult())["text"]