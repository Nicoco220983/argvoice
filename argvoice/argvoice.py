import os
import random
import abc
import functools

from argvoice import MEDIAS_DIR
import argvoice.audio as audio
import argvoice.speech_recognition as speech_recognition
import traceback
import pyttsx3

### INPUTS 

class InputAudio():
    def __init__(self):
        self.val = None
    def ingest_aud(self, aud):
        self.val = aud
    def is_valid(self):
        return self.val is not None


class InputKeyword():
    def __init__(self, keywords_dict):
        self.keywords_dict = keywords_dict
        self.val = None
    def ingest_aud(self, aud):
        self.val = _recognize_keywords(aud, self.keywords_dict)[1]
    def is_valid(self):
        return self.val is not None


### COMMANDS

class ArgumentRecorder():
    def __init__(self, arguments=None, options=None):
        self.args = arguments if arguments else []
        self.args_vals = []
        self.options = options if options else {}
        self.options_vals = {}
        self._current_option = None
    def add_argument(self, arg):
        self.args.append(arg)
    def add_option(self, keyword, arg):
        self.options[keyword] = arg
    def ingest_aud(self, aud):
        if len(self.args_vals) < len(self.args) and (len(self.args_vals) == 0 or self.args[-1].is_complete()):
            arg = self.args_cls[len(self.args)]()
            arg.ingest_aud(aud)
        elif len(self.args) > 0 and (not self.args[-1].is_completed()):
            arg.ingest_aud(aud)
        elif self.opts_cls and (self._current_option is None or self._current_option.is_completed()):
            key = _recognize_keywords(aud, self.opts_cls.keys())
            self._current_option = self.options[key] = self.opts_cls[key]()
        elif (self._current_option is not None) and (not self._current_option.is_completed()):
            self._current_option.ingest_aud(aud)
        else:
            raise InvalidVoiceCommand()
    def is_valid(self):
        return (len(self.args) == len(self.args_cls)) and all(a.is_valid() for a in self.args) and all(a.is_valid() for a in self.options.values())


class CommandsRecorder():
    def __init__(self):
        self.cmds_cls = {}
        self.cmd = None
    def add_command(self, keyword, cmd_class):
        self.cmds_cls[keyword] = cmd_class
    def ingest_aud(self, aud):
        if self.cmd is None:
            key = _recognize_keywords(aud, self.cmds_cls.keys())
            self.cmd = self.cmds_cls[key]()
        elif not cmd.is_completed():
            cmd.ingest_aud(aud)
        else:
            raise InvalidVoiceCommand()
    def is_valid(self):
        return (self.cmd is not None) and self.cmd.is_valid()



MAIN_CMDS = {}

class CmdCoucou(CmdGeneric):
    def run(self):
        say(random.choice([
            "coucou",
            "hello",
            "bonjour",
            "salut",
            "kikoo",
            "salutations",
        ]))
MAIN_CMDS["coucou"] = CmdCoucou

class CmdRepete(CmdGeneric):
    def __init__(self):
        super(CmdRepete, self).__init__()
        self.args = [InputAudio()]
        self.options = Options(ALL_OPTS)
    def run(self):
        self.args[0].val.play()
MAIN_CMDS["répète"] = CmdRepete

class CmdLisMoi(CmdGeneric):
    def __init__(self):
        super(CmdLisMoi, self).__init__()
        self.args = [InputAudio()]
        self.options = Options(ALL_OPTS)
    def run(self):
        print("TODO lis moi :)", len(self.args[0].val))
MAIN_CMDS["lis moi"] = CmdLisMoi



### OPTIONS

class Options():
    def __init__(self, keywords_dict):
        self.keywords_dict = keywords_dict
        self.current_option = None
        self.options = {}
    def add_arg(self, aud):
        if self.current_option is None or self.current_option.is_completed():
            key, opt_cls = _recognize_keywords(aud, self.keywords_dict)
            self.current_option = opt_cls()
            self.options[key] = self.current_option
        else:
            self.current_option.add_arg(aud)
    def is_valid(self):
        return (not self.options) or all(o.is_valid() for o in self.options.values())
    def is_completed(self):
        return False

ALL_OPTS = {}

class OptFois(CmdGeneric):
    def __init__(self):
        super(OptFois, self).__init__()
        self.args = [InputKeyword(NUMS)]
    def run(self):
        print("TODO fois ", self.args[0])
ALL_OPTS["fois"] = OptFois



NUMS = {
    "zéro": 0,
    "un": 1,
    "deux": 2,
    "trois": 3,
    "quatre": 4,
    "cinq": 5,
    "six": 6,
    "sept": 7,
    "huit": 8,
    "neuf": 9,
}


def record_and_recognize(continue_fun=None):

    cmd, completed = None, False
    while True:
        aud0 = audio.AudMicrophone(continue_fun=continue_fun)
        aud = audio.record_next_voice_input(aud0)
        if not continue_fun():
            break
        try:
            if aud is None:
                raise InvalidVoiceCommand()
            if cmd is None:
                cmd = _recognize_keywords(aud, MAIN_CMDS)[1]()
            elif cmd.is_completed():
                raise InvalidVoiceCommand()
            else:
                cmd.add_arg(aud)
            handle_valid_voice_command()
        except InvalidVoiceCommand:
            handle_invalid_voice_command()
    if (not cmd) or (not cmd.is_valid()):
        handle_invalid_voice_command()
    else:
        return cmd


def _recognize_keywords(aud, keywords):
    key = speech_recognition.recognize_keywords(aud, keywords)
    if (not key) or (key not in keywords):
        raise InvalidVoiceCommand()
    return key


def run_cmd(cmd):
    times = 1
    if cmd.options and ("fois" in cmd.options.options):
        times = cmd.options.options["fois"].args[0].val
    for _ in range(times):
        cmd.run()



class InvalidVoiceCommand(Exception):
    pass

OK_AUD = audio.AudFile(os.path.join(MEDIAS_DIR, "ok.wav"))
def handle_valid_voice_command():
    OK_AUD.play()

KO_AUD = audio.AudFile(os.path.join(MEDIAS_DIR, "ko.wav"))
def handle_invalid_voice_command():
    KO_AUD.play()

@functools.lru_cache()
def init_pyttsx3():
    engine = pyttsx3.init()
    try:
        voice = next(v for v in engine.getProperty('voices') if 'fr_FR' in v.languages)
        engine.setProperty("voice", voice.id)
    except StopIteration:
        pass
    return engine

def say(txt):
    engine = init_pyttsx3()
    engine.say(txt)
    engine.runAndWait()