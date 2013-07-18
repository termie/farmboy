# vim: tabstop=4 shiftwidth=4 softtabstop=4
import fabtools.require

from contrail import util


from fabric.api import roles
from fabric.api import task


@roles('proxy')
@task
def deploy():
    """Deploy all the proxy server bits."""
    fabtools.require.deb.packages([
        'haproxy'
    ])

    fabtools.require.files.file(
        source   = util.files('haproxy/haproxy.base'),
        path     = '/etc/haproxy/haproxy.cfg',
        owner    = 'root',
        group    = 'root',
        mode     = '644',
        use_sudo = True)

    fabtools.require.files.file(
        source   = util.files('haproxy/default'),
        path     = '/etc/default/haproxy',
        owner    = 'root',
        group    = 'root',
        mode     = '644',
        use_sudo = True)

    fabtools.require.service.restarted('haproxy')
