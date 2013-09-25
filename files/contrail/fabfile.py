# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os

from contrail import aptcacher
from contrail import core
from contrail import django
from contrail import gitlab
from contrail import gunicorn
from contrail import haproxy
from contrail import jenkins
from contrail import nginx
from contrail import tomcat
from contrail import util
from contrail import vagrant


from fabric.api import env
from fabric.api import execute
from fabric.api import task


# Private key that we'll use to connect to the machines
env.key_filename = os.path.expanduser('~/.vagrant.d/insecure_private_key')

# Since we're be using apt caching, point out where that proxy will live.
# POWER TIP: If you're already using such a proxy, you can just point this
#            at that server and skip the `execute(aptcacher.deploy)` step.
env.contrail_apt_proxy = %(apt_proxy)s

# Define which servers go with which roles.
# POWER TIP: These can defined as callables as well if you want to load
#            the servers in some more dynamic way.
# POWER TIP: You might also want to separate these out into a yaml file
#            and do `env.roledefs = yaml.load(open('contrail.yaml'))`
#            or use the helper `env.roledefs = util.load_roledefs()`
env.roledefs.update(%(roledefs)s)

# Where our django app lives (this directory will be pushed to web servers).
# POWER TIP: We expect this to be in the current directory by default
#            but a full path works here, too.
# POWER TIP: You can set the path directly as we do below in the execute
#            call, but if none is set it will default to using the this
#            env variable.
env.contrail_django_app = 'demo'

# Where to find the template files to use when configuring services.
# POWER TIP: We'll fall back to the defaults shipped with contrail for
#            any files not found in this location.
# POWER TIP: TODO(termie) Use `contrail files $some_module` to get the
#            list and locations of files used for a given module.
env.contrail_files = './files'


