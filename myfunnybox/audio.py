import time
import pyaudio
import wave
import numpy as np
import noisereduce as nr

PA_FORMAT = pyaudio.paInt16  # this is the format supported by MCUsphinx model
NP_FORMAT = np.int16
CHANNELS = 1  # no need of stereo
RATE = 16000  # default sampling rate of MCUsphinx (should keep this one)
CHUNK = 4096  # try to have around 4 chunks by second

REDUCE_NOISE_WARMUP_DURATION = .5
SILENCE_SPLIT_DURATION = .5
SILENCE_AMPLITUDE = 1000


def record_next_voice_input(max_duration=10):
    while True:
        # record microphone
        aud = np.empty(1, dtype=NP_FORMAT)
        always_silent = True
        for i, aud_chunk in enumerate(record_gen(max_duration)):
            aud = np.append(aud, aud_chunk)
            # reduce noise
            # do it on full aud at each iteration, as it offers far better results
            if i < RATE / CHUNK * REDUCE_NOISE_WARMUP_DURATION:
                continue
            aud_wo_noise = nr.reduce_noise(y=aud, sr=RATE, stationary=True)
            is_split_silence = is_silence(aud_wo_noise[-int(RATE*SILENCE_SPLIT_DURATION):])
            always_silent = always_silent and is_split_silence
            # stop when user spoke, then returned to silence
            if (not always_silent) and is_split_silence:
                break
        # ignore first chunk because of strange noise
        aud_wo_noise = aud_wo_noise[CHUNK:]
        # trim silence at start and end of audio
        nb_frames = int(len(aud_wo_noise)/CHUNK)
        start = next(i for i in range(nb_frames) if not is_silence(aud_wo_noise[(i*CHUNK):((i+1)*CHUNK)]))
        start = max(0, start-1)
        end = next(i for i in range(nb_frames) if not is_silence(aud_wo_noise[(-(i+1)*CHUNK):(-i*CHUNK or None)]))
        end = max(0, end-1)
        aud_wo_noise = aud_wo_noise[(start*CHUNK):(-end*CHUNK or None)]
        if len(aud_wo_noise) == 0:
            continue
        yield aud


def is_silence(aud):
    amplitude = np.percentile(np.square(aud), 80)
    return amplitude < SILENCE_AMPLITUDE


def record_gen(max_duration=None):
    pyaud = pyaudio.PyAudio()

    stream = pyaud.open(
        format=PA_FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    print("Start recording...", end='', flush=True)
    i = 0
    while True:
        if (max_duration is not None) and (i>= int(RATE / CHUNK * max_duration)):
            break
        i += 1
        yield raw_to_np(stream.read(CHUNK, exception_on_overflow = False))
    print(" [done]")

    stream.stop_stream()
    stream.close()
    pyaud.terminate()


def record(*args, **kwargs):
    return np.array(list(record_gen(*args, **kwargs))).flatten()


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
    stream_out.write(np_to_raw(aud))
    time.sleep(0.2)
    stream_out.stop_stream()
    stream_out.close()
    pyaud.terminate()


def save(aud, fpath):
    wf = wave.open(fpath, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pyaudio.get_sample_size(PA_FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(np_to_raw(aud))
    wf.close()


def open(fpath):
    w = wave.open(fpath, 'r')
    raw = b"".join(
        w.readframes(i)
        for i in range(w.getnframes())
    )
    return raw_to_np(raw)


def raw_to_np(val):
    return np.frombuffer(val, dtype=NP_FORMAT)

def np_to_raw(val):
    return val.astype(NP_FORMAT).tobytes()

def reduce_noise(aud):
    aud_np = raw_to_np(aud)
    out_np = nr.reduce_noise(y=aud_np, sr=RATE, stationary=True)
    return np_to_raw(out_np)