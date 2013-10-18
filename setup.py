try:
    from setuptools import setup
except:
    from distutils.core import setup

config = dict(
    name='farmboy',
    version='0.1.0',
    url='https://github.com/termie/farmboy',
    description='Rapid development environments.',
    author='Andy Smith',
    author_email='github@anarkystic.com',
    install_requires=['fabric', 'fabtools'],
    packages=['farmboy'],
    entry_points={
        'console_scripts': [
            'farmboy = farmboy.cli:main',
        ],
    },
)

setup(**config)
