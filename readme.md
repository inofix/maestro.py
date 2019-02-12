# Maestro (python)

# Development

The entry point of the applicationis `./main.py`

## Dependencies management, with `pip`

Dependencies are listed in `./requirements.txt`.
We install them through `pip`, python's package manager.

## Environement management with `virtualenv`

Source: https://click.palletsprojects.com/en/7.x/quickstart/

We install `virtualenv`. It enables multiple side-by-side
installations of Python and librairies, one for each project. It
doesn’t actually install separate copies of Python, but it does
provide a clever way to keep different project environments
isolated.

`sudo pip install virtualenv`

Now, whenever we want to work on a project, we only have to activate the corresponding environment

`. venv/bin/activate`

To stop working on the project:

`deactivate`

## Modules, `setuptools` integration

> When writing command line utilities, it’s recommended to write them
> as modules that are distributed with setuptools instead of using Unix
> shebangs.
Source: https://click.palletsprojects.com/en/7.x/setuptools/#setuptools-integration


In `./setup.py` is written the setup for the application.

## Test the script

To test the script we can make a new virtualenv and then install our package:

```
virtualenv venv
. venv/bin/activate
pip install --editable .
```

Afterwards, the command should be available as `maestro`

Note: the `pip install --editable` command, is suffixed with a `.`
(dot); the `venv/bin/activate`, prefixed with a `.`; it represents the
current directory in unix systems.
