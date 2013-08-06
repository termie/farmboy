# vim: tabstop=4 shiftwidth=4 softtabstop=4

from fabric.api import env
from fabric.api import parallel
from fabric.api import roles
from fabric.api import task

import fabtools.deb
import fabtools.require


DEFAULT_USER='contrail'


def _set_env_defaults():
    env.setdefault('contrail_user', DEFAULT_USER)
    env.setdefault('contrail_files', './files')
    env['skip_bad_hosts'] = True
    env['timeout'] = 2


_set_env_defaults()


@roles('proxy', 'web')
@task
@parallel
def install_user(user=DEFAULT_USER):
    env.contrail_user = user
    fabtools.require.user(user, shell='/bin/bash')
    fabtools.deb.update_index(quiet=False)
