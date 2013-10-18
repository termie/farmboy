# vim: tabstop=4 shiftwidth=4 softtabstop=4
import fabtools.require

from farmboy import util


from fabric.api import env
from fabric.api import roles
from fabric.api import task


WEB_SERVER = '  server web%(i)s %(host)s:%(port)s maxconn 32'


@roles('proxy')
@task
def deploy():
    """Add HAproxy to the <proxy> host."""
    fabtools.require.deb.packages([
        'haproxy'
    ])

    servers = []
    for i, server in enumerate(env.roledefs['web']):
        server_s = WEB_SERVER % {'i': i,
                                 'host': server.split('@')[-1],
                                 'port': '80'}
        servers.append(server_s)

    fabtools.require.files.template_file(
        template_source   = util.files('haproxy/haproxy.base'),
        context  = {'servers': '\n'.join(servers)},
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
