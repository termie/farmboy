try:
    from setuptools import setup
except:
    from distutils.core import setup

config = dict(
    name='stableboy',
    version='0.1.0',
    url='https://github.com/termie/stableboy',
    description='Rapid development environments.',
    author='Andy Smith',
    author_email='github@anarkystic.com',
    install_requires=['fabric', 'fabtools'],
    packages=['stableboy'],
    entry_points={
        'console_scripts': [
            'stableboy = stableboy.cli:main',
        ],
    },
)

setup(**config)
