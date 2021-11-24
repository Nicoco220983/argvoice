import os
import functools
import json
# from pocketsphinx import LiveSpeech, get_model_path
# from pocketsphinx.pocketsphinx import *
# from sphinxbase.sphinxbase import *

from argvoice import MODELS_DIR

import vosk

# VOICE_COMMANDS = {
#     "main": ["coucou", "répète", "lis moi"],
#     "option": ["fois"],
#     "num": ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
# }
# VOICE_COMMANDS["_all"] = sum((v for v in VOICE_COMMANDS.values()), [])

MODEL = "vosk-model-small-fr-pguyot-0.3"

@functools.lru_cache()
def init_model(model):
    return vosk.Model(os.path.join(MODELS_DIR, model))

@functools.lru_cache()
def init_recognizer(keywords, rate, model=MODEL):
    _model = init_model(model)
    return vosk.KaldiRecognizer(_model, rate, f'["{" ".join(keywords)}", "[unk]"]')

def recognize_keywords(aud, keywords):
    rec = init_recognizer(tuple(sorted(keywords)), aud.rate)
    rec.AcceptWaveform(aud.get_raw())
    return json.loads(rec.FinalResult())["text"].strip()
