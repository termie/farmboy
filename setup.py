try:
    from setuptools import setup
except:
    from distutils.core import setup

config = dict(
    name='contrail',
    version='0.1.0',
    url='https://github.com/termie/contrail',
    description='Rapid development environments.',
    author='Andy Smith',
    author_email='github@anarkystic.com',
    install_requires=['fabric', 'fabtools'],
    packages=['contrail'],
    entry_points={
        'console_scripts': [
            'contrail = contrail.cli:main',
        ],
    },
)

setup(**config)
