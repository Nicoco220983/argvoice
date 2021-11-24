import time
import pyaudio
import wave
import numpy as np
import noisereduce as nr
import abc
import functools

PA_FORMAT = pyaudio.paInt16  # this is the format supported by MCUsphinx model
NP_FORMAT = np.int16
CHANNELS = 1  # no need of stereo
RATE = 16000  # default sampling rate of MCUsphinx (should keep this one)
CHUNK = 4096

REDUCE_NOISE_WARMUP_DURATION = .5
SILENCE_SPLIT_DURATION = .5
SILENCE_AMPLITUDE = 1000

PA_NP_FORMATS = [
    (pyaudio.paInt16, np.dtype('int16')),
    (pyaudio.paInt32, np.dtype('int32')),
]
PA_TO_NP_FORMATS = {f[0]:f[1] for f in PA_NP_FORMATS}
NP_TO_PA_FORMATS = {f[1]:f[0] for f in PA_NP_FORMATS}


@functools.lru_cache()
def init_pyaudio():
    return pyaudio.PyAudio()


class Audio():

    def __init__(self):
        self.format = PA_FORMAT
        self.channels = 1
        self.rate = RATE

    @abc.abstractmethod
    def get_raw_gen(self):
        ...
    @functools.lru_cache()
    def get_raw(self):
        return b"".join(self.get_raw_gen())
    def get_np_gen(self):
        for raw in self.get_raw_gen():
            yield np.frombuffer(raw, dtype=PA_TO_NP_FORMATS[self.format])
    def get_np(self):
        raw = self.get_raw()
        return np.frombuffer(raw, dtype=PA_TO_NP_FORMATS[self.format])
    
    def play(self):
        pyaud = init_pyaudio()
        stream_out = pyaud.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=False,
            output=True
        )
        stream_out.start_stream()
        stream_out.write(self.get_raw())
        time.sleep(0.2)
        stream_out.stop_stream()
        stream_out.close()
    
    def save(self, ofpath):
        wfile = wave.open(ofpath, 'wb')
        wfile.setnchannels(self.channels)
        wfile.setsampwidth(pyaudio.get_sample_size(self.format))
        wfile.setframerate(self.rate)
        for raw in self.get_raw_gen():
            wfile.writeframes(raw)
        wfile.close()


class AudMicrophone(Audio):

    def __init__(self, continue_fun=None):
        Audio.__init__(self)
        self.continue_fun = continue_fun

    def get_raw_gen(self):
        pyaud = init_pyaudio()

        stream = pyaud.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=CHUNK
        )
        while True:
            if (self.continue_fun is not None) and (not self.continue_fun()):
                break
            yield stream.read(CHUNK, exception_on_overflow = False)

        stream.stop_stream()
        stream.close()


class AudFile(Audio):

    def __init__(self, fpath):
        self.wfile = wave.open(fpath,"rb")
        self.format = pyaudio.get_format_from_width(self.wfile.getsampwidth())
        self.channels = self.wfile.getnchannels()
        self.rate = self.wfile.getframerate()

    def get_raw_gen(self):
        for i in range(self.wfile.getnframes()):
            yield self.wfile.readframes(i)


class AudNumpy(Audio):

    def __init__(self, np_aud, rate=RATE):
        self.format = NP_TO_PA_FORMATS[np_aud.dtype]
        self.channels = 1
        self.rate = rate
        self.np_aud = np_aud

    def get_np_gen(self):
        yield self.np_aud
    def get_np(self):
        return self.np_aud
    def get_raw_gen(self):
        for np_aud in self.get_np_gen():
            yield np_aud.tobytes()
    def get_raw(self):
        return self.get_np().tobytes()


def record_next_voice_input(aud):
    # record microphone
    np_aud = np.empty(1, dtype=NP_FORMAT)
    np_aud_wo_noise = np.empty(1, dtype=NP_FORMAT)
    always_silent = True
    print("Start recording voice input...", end='', flush=True)
    for np_aud_chunk in aud.get_np_gen():
        np_aud = np.append(np_aud, np_aud_chunk)
        # reduce noise
        # do it on full aud at each iteration, as it offers far better results
        if len(np_aud) < RATE * REDUCE_NOISE_WARMUP_DURATION:
            continue
        if len(np_aud) - len(np_aud_wo_noise) < RATE * 0.25:
            continue
        np_aud_wo_noise = nr.reduce_noise(y=np_aud, sr=aud.rate, stationary=True)
        is_split_silence = is_silence(np_aud_wo_noise[-int(RATE*SILENCE_SPLIT_DURATION):])
        always_silent = always_silent and is_split_silence
        # stop when user spoke, then returned to silence
        if (not always_silent) and is_split_silence:
            break
    print(" [done]")
    # ignore first chunk because of strange noise
    if len(np_aud_wo_noise) < len(np_aud):
        np_aud_wo_noise = nr.reduce_noise(y=np_aud, sr=aud.rate, stationary=True)
    np_aud_wo_noise = np_aud_wo_noise[CHUNK:]
    # trim silence at start and end of audio
    nb_frames = int(len(np_aud_wo_noise)/CHUNK)
    try:
        start = next(i for i in range(nb_frames) if not is_silence(np_aud_wo_noise[(i*CHUNK):((i+1)*CHUNK)]))
        start = max(0, start-1)
        end = next(i for i in range(nb_frames) if not is_silence(np_aud_wo_noise[(-(i+1)*CHUNK):(-i*CHUNK or None)]))
        end = max(0, end-1)
        np_aud_wo_noise = np_aud_wo_noise[(start*CHUNK):(-end*CHUNK or None)]
    except StopIteration:
        np_aud_wo_noise = np.empty(1, dtype=NP_FORMAT)
    return AudNumpy(np_aud, rate=aud.rate) if len(np_aud) else None


def is_silence(np_aud):
    amplitude = np.percentile(np.square(np_aud), 80)
    return amplitude < SILENCE_AMPLITUDE


# def record_gen(continue_fun=None):
#     pyaud = init_pyaudio()

#     stream = pyaud.open(
#         format=PA_FORMAT,
#         channels=CHANNELS,
#         rate=RATE,
#         input=True,
#         frames_per_buffer=CHUNK
#     )
#     while True:
#         if (continue_fun is not None) and (not continue_fun()):
#             break
#         yield raw_to_np(stream.read(CHUNK, exception_on_overflow = False))

#     stream.stop_stream()
#     stream.close()


# def record(*args, **kwargs):
#     return np.array(list(record_gen(*args, **kwargs))).flatten()


# def play(aud):
#     pyaud = init_pyaudio()
#     stream_out = pyaud.open(
#         format=aud.format,
#         channels=aud.channels,
#         rate=aud.rate,
#         input=False,
#         output=True
#     )
#     stream_out.start_stream()
#     for raw in aud.get_raw_gen():
#         stream_out.write(raw)
#     time.sleep(0.2)
#     stream_out.stop_stream()
#     stream_out.close()


# def save(aud, fpath):
#     wf = wave.open(fpath, 'wb')
#     wf.setnchannels(aud.channels)
#     wf.setsampwidth(pyaudio.get_sample_size(PA_FORMAT))
#     wf.setframerate(aud.rate)
#     wf.writeframes(np_to_raw(aud))
#     wf.close()


# def open(fpath):
#     w = wave.open(fpath, 'r')
#     raw = b"".join(
#         w.readframes(i)
#         for i in range(w.getnframes())
#     )
#     return raw_to_np(raw)


# def raw_to_np(val):
#     return np.frombuffer(val, dtype=NP_FORMAT)

# def np_to_raw(val):
#     return val.astype(NP_FORMAT).tobytes()

# def reduce_noise(aud):
#     aud_np = raw_to_np(aud)
#     out_np = nr.reduce_noise(y=aud_np, sr=RATE, stationary=True)
#     return np_to_raw(out_np)