# vim: tabstop=4 shiftwidth=4 softtabstop=4

from fabric.api import env
from fabric.api import parallel
from fabric.api import roles
from fabric.api import task

import fabtools.deb
import fabtools.require


DEFAULT_USER='farmboy'


def _set_env_defaults():
    env.setdefault('farmboy_user', DEFAULT_USER)
    env.setdefault('farmboy_files', './files')
    env.skip_bad_hosts = True
    env.timeout = 2
    env.roledefs = {'apt': [], 'ci': [], 'proxy': [], 'vcs': [], 'web': []}


_set_env_defaults()


@roles('proxy', 'web')
@task
@parallel
def install_user(user=DEFAULT_USER):
    """Ensure our default user has been created on all hosts."""
    env.farmboy_user = user
    fabtools.require.user(user, shell='/bin/bash')
    fabtools.deb.update_index(quiet=False)
