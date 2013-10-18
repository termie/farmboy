# vim: tabstop=4 shiftwidth=4 softtabstop=4

# This is a templated file generated from files/stableboy/fabfile.py,
# by commands such as `stableboy vagrant.init` will produce an output
# version in your local directory that you can then modify to your
# heart's content.

import os

from stableboy import aptcacher
from stableboy import aws
from stableboy import core
from stableboy import django
from stableboy import gitlab
from stableboy import gunicorn
from stableboy import haproxy
from stableboy import jenkins
from stableboy import nginx
from stableboy import tomcat
from stableboy import util
from stableboy import vagrant


from fabric.api import env
from fabric.api import execute
from fabric.api import task

%(preamble)s

# Private key that we'll use to connect to the machines
env.key_filename = %(keyfile)s

# Define which servers go with which roles.
# POWER TIP: These can defined as callables as well if you want to load
#            the servers in some more dynamic way.
# POWER TIP: You might also want to separate these out into a yaml file
#            and do `env.roledefs = yaml.load(open('stableboy.yaml'))`
#            or use the helper `env.roledefs = util.load_roledefs()`
env.roledefs.update(%(roledefs)s)

# Since we're be using apt caching, point out where that proxy will live.
# POWER TIP: If you're already using such a proxy, you can just point this
#            at that server and skip the `execute(aptcacher.deploy)` step.
if env.roledefs['apt']:
    apt = env.roledefs['apt'][0]
    env.stableboy_apt_proxy = 'http://%%s:3142' %% util.host(apt)

# Where our django app lives (this directory will be pushed to web servers).
# This is expected to be the directory that contains the manage.py file for
# a default django setup.
# POWER TIP: We expect this to be in the current directory by default
#            but a full path works here, too.
# POWER TIP: You can set the path directly as we do below in the execute
#            call, but if none is set it will default to using the this
#            env variable.
env.stableboy_django_app = 'demo'

# Where to find the template files to use when configuring services.
# POWER TIP: We'll fall back to the defaults shipped with stableboy for
#            any files not found in this location.
# POWER TIP: TODO(termie) Use `stableboy files $some_module` to get the
#            list and locations of files used for a given module.
env.stableboy_files = './files'


@task(default=True)
def demo():
    if env.roledefs['apt']:
        execute(aptcacher.deploy)
        execute(aptcacher.set_proxy)
    execute(core.install_user)
    execute(haproxy.deploy)
    execute(nginx.deploy)
    execute(gunicorn.deploy)
    execute(django.deploy, path=env.stableboy_django_app)

    print ('Alright! Check out your site at: http://%%s'
            %% util.host(env.roledefs['proxy'][0]))
