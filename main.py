import click

from maestro import settings

@click.group()
def main():
    pass

@main.command()
def init():
    click.echo('Init command')
    do_reinit()

@main.command()
def reinit():
    do_reinit()

def do_reinit():
    pass
