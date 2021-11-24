#!/usr/bin/env python
import os
import click
import time
import threading

from myfunnybox import TESTS_DATA_DIR
import myfunnybox.main as main
import myfunnybox.audio as audio

@click.group()
def cli():
    pass


@cli.command("record_command")
@click.argument("name")
@click.option("-d", "--duration", default=3)
@click.option("-n", "--times", default=10)
def record_command(name, duration, times):
    for i in range(times):
        start = time.time()
        aud = audio.AudMicrophone(continue_fun=lambda: time.time() - start < duration)
        aud.save(os.path.join(TESTS_DATA_DIR, f"voice_commands/{name}_{i}.wav"))


@cli.command("micro_test")
@click.argument("keywords", nargs=-1)
def micro_test(keywords):
    keyListener = KeyboardInutListerner()
    keyListener.start()
    aud0 = audio.AudMicrophone(continue_fun=lambda: not keyListener.pressed)
    for aud in audio.record_next_voice_input(aud0):
        cmd = speech_recognition.recognize_keywords(aud, keywords)
        if cmd:
            print(cmd)


@cli.command("record_and_recognize")
def record_and_recognize():
    keyListener = KeyboardInutListerner()
    keyListener.start()
    main.record_and_recognize(continue_fun=lambda: not keyListener.pressed)


class KeyboardInutListerner(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.pressed = False
    def run(self):
        input()
        self.pressed = True


if __name__ == '__main__':
    cli()