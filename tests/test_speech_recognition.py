import os
import unicodedata
import pytest

from myfunnybox import TESTS_DATA_DIR
import myfunnybox.main as main
import myfunnybox.audio as audio
import myfunnybox.speech_recognition as speech_recognition


def norm_voice_command(val):
    return strip_accents(val).replace(" ","_")

def strip_accents(val):
   return ''.join(
        c for c in unicodedata.normalize('NFD', val)
        if unicodedata.category(c) != 'Mn'
    )


def _to_params(keywords):
    return [
        (tuple(keywords), keyword, num)
        for keyword in keywords
        for num in range(10)
    ]
@pytest.mark.parametrize("keywords, keyword, num",
    _to_params(main.MAIN_CMDS.keys()) + _to_params(main.ALL_OPTS.keys()) + _to_params(main.NUMS.keys())
)
def test_recognize_keywords(keywords, keyword, num):
    audpath = os.path.join(TESTS_DATA_DIR, f"voice_commands/{norm_voice_command(keyword)}_{num}.wav")
    aud0 = audio.AudFile(audpath)
    aud = audio.record_next_voice_input(aud0)
    res_cmd = speech_recognition.recognize_keywords(aud, keywords)
    assert keyword == res_cmd