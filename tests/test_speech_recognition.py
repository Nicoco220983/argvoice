import os
import unicodedata
import pytest
from unittest.mock import patch

from myfunnybox import TESTS_DATA_DIR
import myfunnybox.audio as audio
import myfunnybox.speech_recognition as speech_recognition


def norm_voice_command(val):
    return strip_accents(val).replace(" ","_")

def strip_accents(val):
   return ''.join(
        c for c in unicodedata.normalize('NFD', val)
        if unicodedata.category(c) != 'Mn'
    )


@pytest.mark.parametrize("voice_commands_key, voice_command, num", [
    (voice_commands_key, voice_command, num)
    for voice_commands_key in speech_recognition.VOICE_COMMANDS.keys()
    for voice_command in speech_recognition.VOICE_COMMANDS[voice_commands_key]
    for num in range(10)
])
@patch('myfunnybox.audio.record_gen')
def test_recognize_voice_command(mocked_record_gen, voice_commands_key, voice_command, num):
    audpath = os.path.join(TESTS_DATA_DIR, f"voice_commands/{norm_voice_command(voice_command)}_{num}.wav")
    def fake_record_gen(duration):
        aud = audio.open(audpath)
        for i in range(int(len(aud)/audio.CHUNK)):
            yield aud[(i*audio.CHUNK):((i+1)*audio.CHUNK)]
    mocked_record_gen.side_effect = fake_record_gen
    aud = next(audio.record_next_voice_input())
    res_cmd = speech_recognition.recognize_voice_command(voice_commands_key, aud)
    assert voice_command == res_cmd