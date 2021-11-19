#!/usr/bin/env python
import os
import click

from myfunnybox import TEST_DATA_DIR
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
        aud = audio.record(duration)
        audio.save(aud, os.path.join(TEST_DATA_DIR, f"voice_commands/{name}_{i}.wav"))

@cli.command("micro_test")
def micro_test():
    for cmd in main.record_and_recognize():
        if cmd:
            print(cmd)


if __name__ == '__main__':
    cli()