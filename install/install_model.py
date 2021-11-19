#!/usr/bin/env python
import os
import urllib.request
import zipfile

from myfunnybox import MODELS_DIR
from myfunnybox.speech_recognition import MODEL

MODEL_PATH = os.path.join(MODELS_DIR, MODEL)

if not os.path.exists(MODEL_PATH):

    try:
        os.makedirs(MODELS_DIR)
    except FileExistsError:
        pass
    
    model_url = f"https://alphacephei.com/vosk/models/{MODEL}.zip"
    print(f"Downloading {model_url}...", end='', flush=True)
    urllib.request.urlretrieve(model_url, f"{MODEL_PATH}.zip")
    print(" [done]")

    with zipfile.ZipFile(f"{MODEL_PATH}.zip", 'r') as zip_ref:
        zip_ref.extractall(MODELS_DIR)

    os.remove(f"{MODEL_PATH}.zip")

    print("Model installed")

else:
    print("Model already installed")