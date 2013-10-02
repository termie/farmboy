# vim: tabstop=4 shiftwidth=4 softtabstop=4

#import shutil

from contrail import util

from fabric.api import env
from fabric.api import local
from fabric.api import task


DEFAULT_ROLEDEFS = {
    'proxy': ['vagrant@192.168.33.10'],
    'vcs': ['vagrant@192.168.33.11'],
    'ci': ['vagrant@192.168.33.12'],
    'apt': ['vagrant@192.168.33.13'],
    'web': ['vagrant@192.168.33.100',
            'vagrant@192.168.33.101'],
    'tomcat': ['vagrant@192.168.33.100',
               'vagrant@192.168.33.101']}

DEFAULT_APT_PROXY = 'http://192.168.33.13:3142'

KEYFILE_S = "os.path.expanduser('~/.vagrant.d/insecure_private_key')"


@task
def init():
    """Copy vagrant-specific template to local directory."""
    vagrantfile = util.files('vagrant/Vagrantfile')

    # TODO(termie): local cp or shutil?
    local('cp %s %s' % (vagrantfile, './Vagrantfile'))
    #shutil.copy(vagrantfile, './Vagrantfile')
    fabfile_context = {'roledefs': repr(DEFAULT_ROLEDEFS),
                       'keyfile': KEYFILE_S,
                       'preamble': '',
                       }
    util.template_file('contrail/fabfile.py', 'fabfile.py', fabfile_context)


@task
def build():
    local('vagrant up')
