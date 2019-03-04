from setuptools import setup

setup(
    name='maestro',
    version='0.1',
    py_modules=['maestro'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        maestro=main:main
    ''',
)
