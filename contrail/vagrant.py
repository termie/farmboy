# vim: tabstop=4 shiftwidth=4 softtabstop=4

from fabric.api import env
from fabric.api import local
from fabric.api import task


DEFAULT_ROLEDEFS = {
    'proxy': ['vagrant@192.168.33.10'],
    'vcs': ['vagrant@192.168.33.11'],
    'web': ['vagrant@192.168.33.100',
            'vagrant@192.168.33.101'],
    'tomcat': ['vagrant@192.168.33.100',
               'vagrant@192.168.33.101']}


@task
def defaults():
    env.roledefs = DEFAULT_ROLEDEFS
    result = local('vagrant ssh-config proxy | grep IdentityFile',
                   capture=True)
    env.key_filename = result.split()[1].strip('"')
