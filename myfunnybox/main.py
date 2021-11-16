import os
import time
import math
from copy import copy
import pyaudio
from pocketsphinx import LiveSpeech, get_model_path
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *
import numpy as np
import noisereduce as nr

HERE = os.path.abspath(os.path.dirname(__file__))
MODELDIR = get_model_path()

PA_FORMAT = pyaudio.paFloat32
NP_FORMAT = np.float32
CHANNELS = 1
RATE = 16000
CHUNK = 1024

SILENCE_SPLIT_DURATION = .5
SILENCE_AMPLITUDE = 0.01

def main():

    arg_auds = [
        record_next_arg(os.getenv("RECORD_TIME", 10))
        for _ in range(3)
    ]
    for aud in arg_auds:
        print("TMP")
        play(np_to_aud(aud))


    # in_speech_bf = False
    # decoder.start_utt()
    # while True:
    #     buf = stream.read(1024)
    #     if buf:
    #         print("TMP buf ampl", _mean_sqrt(buf))
    #         decoder.process_raw(buf, False, False)
    #         if decoder.get_in_speech() != in_speech_bf:
    #             in_speech_bf = decoder.get_in_speech()
    #             if not in_speech_bf:
    #                 decoder.end_utt()
    #                 print('Result:', decoder.hyp().hypstr)
    #                 decoder.start_utt()
    #     else:
    #         break
    # decoder.end_utt()


def record_next_arg(duration):
    pyaud = pyaudio.PyAudio()
    stream = pyaud.open(
        format=PA_FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    print("Start recording...", end='', flush=True)
    aud = np.empty(1, dtype=NP_FORMAT)
    arg_start = None
    for i in range(0, int(RATE / CHUNK * duration)):
        aud_chunk = aud_to_np(stream.read(CHUNK))
        aud = np.append(aud, aud_chunk)
        # reduce noise on full aud at each iteration, as it offers far better results
        aud_wo_noise = nr.reduce_noise(y=aud, sr=RATE, stationary=True)
        end_amplitude = np.square(aud_wo_noise[-int(RATE*SILENCE_SPLIT_DURATION):]).mean()
        is_silence = end_amplitude < SILENCE_AMPLITUDE
        if (not is_silence) and (arg_start is None):
            arg_start = i
        if (arg_start is not None) and is_silence:
            break
    print(" [done]")
    # keep only not silent part
    add_frames = int(RATE*0.2) # this not to cut to hard
    return aud_wo_noise[
        max(0, (arg_start*CHUNK)-add_frames)
        :min(0, -int(RATE*SILENCE_SPLIT_DURATION)+add_frames)
    ]




def record(duration):
    pyaud = pyaudio.PyAudio()

    ite, frames = 0, []
    nb_frames = int(RATE / CHUNK * duration)

    stream = pyaud.open(
        format=PA_FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    print("Start recording...", end='', flush=True)
    aud = b"".join(
        stream.read(CHUNK)
        for _ in range(0, int(RATE / CHUNK * duration))
    )
    print(" [done]")

    stream.stop_stream()
    stream.close()
    pyaud.terminate()

    return aud


def play(aud):
    pyaud = pyaudio.PyAudio()
    stream_out = pyaud.open(
        format=PA_FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=False,
        output=True
    )
    stream_out.start_stream()
    stream_out.write(aud)
    time.sleep(0.2)
    stream_out.stop_stream()
    stream_out.close()
    pyaud.terminate()


def aud_to_np(val):
    return np.frombuffer(val, dtype=NP_FORMAT)

def np_to_aud(val):
    return val.astype(NP_FORMAT).tobytes()

def reduce_noise(aud):
    aud_np = aud_to_np(aud)
    out_np = nr.reduce_noise(y=aud_np, sr=RATE, stationary=True)
    return np_to_aud(out_np)


def init_voice_recognition():
    config = Decoder.default_config()
    config.set_string('-hmm', os.path.join(HERE, '../models', 'cmusphinx-fr-5.2'))
    config.set_string('-lm', os.path.join(HERE, '../models', 'fr-small.lm.bin'))
    config.set_string('-dict', os.path.join(HERE, '../models', 'fr_tiny.dict'))
    return Decoder(config)


if __name__ == "__main__":
    main()