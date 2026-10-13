#!/usr/bin/env python3
from setuptools import setup

APP = ['packaging/scripts/whisper_doped_app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,  # Menu bar app doesn't need argv emulation
    'iconfile': 'assets/WhisperDoped.icns',
    'plist': {
        'CFBundleName': 'WhisperDoped',
        'CFBundleDisplayName': 'Whisper Doped',
        'CFBundleIdentifier': 'com.whisperdoped.app',
        'CFBundleVersion': '0.2.0',
        'CFBundleShortVersionString': '0.2.0',
        'LSUIElement': True,  # Runs as menu bar/agent app, no dock icon
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15.0',
        'NSHumanReadableCopyright': 'MIT License',
    },
    'packages': ['whisper_doped'],
    'includes': [
        'rumps',
        'numpy',
        'sounddevice',
        'pynput',
        'pyobjc',
        'Cocoa',
        'Quartz',
        'ApplicationServices',
        'Foundation',
    ],
    'excludes': [
        'matplotlib',
        'IPython',
        'jupyter',
        'tkinter',
        'test',
        'unittest',
    ],
}

setup(
    name='WhisperDoped',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
