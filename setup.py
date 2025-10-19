from setuptools import setup, find_packages

setup(
    name="halloween-leds",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pygame",
        "aiohttp",
        "pyyaml",
        "python-dotenv",
        "librosa",
        "numpy",
        "matplotlib",
    ],
    entry_points={
        'console_scripts': [
            'music-sync=halloween_leds.music_sync:main',
            'preset-upload=halloween_leds.wled_preset_uploader:main',
        ],
    },
)
