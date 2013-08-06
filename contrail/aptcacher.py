# vim: tabstop=4 shiftwidth=4 softtabstop=4

import fabtools.deb
import fabtools.require

from contrail import util


from fabric.api import env
from fabric.api import parallel
from fabric.api import roles
from fabric.api import task



def _set_env_defaults():
    env.setdefault('contrail_apt_host', '192.168.11.13')
    env.setdefault('contrail_apt_port', '3142')


_set_env_defaults()


@roles('apt')
@task
def deploy():
    fabtools.require.deb.packages([
        'apt-cacher'
    ])

    fabtools.require.files.file(
        source   = util.files('apt-cacher/default'),
        path     = '/etc/default/apt-cacher',
        owner    = 'root',
        group    = 'root',
        mode     = '644',
        use_sudo = True)

    fabtools.require.files.file(
        source   = util.files('apt-cacher/apt-cacher.conf'),
        path     = '/etc/apt-cacher/apt-cacher.conf',
        owner    = 'root',
        group    = 'root',
        mode     = '644',
        use_sudo = True)

    fabtools.require.service.restarted('apt-cacher')


@roles('ci', 'proxy', 'vcs', 'web')
@task
@parallel
def set_proxy():
    # TODO(termie): template this with host and port above
    fabtools.require.files.file(
        source   = util.files('apt-cacher/01apt-cacher'),
        path     = '/etc/apt/apt.conf.d/01apt-cacher',
        owner    = 'root',
        group    = 'root',
        mode     = '644',
        use_sudo = True)
