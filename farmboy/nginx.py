# vim: tabstop=4 shiftwidth=4 softtabstop=4
import fabtools.nginx
import fabtools.require

from farmboy import util


from fabric.api import parallel
from fabric.api import roles
from fabric.api import task


@roles('web')
@task
@parallel
def deploy():
    """Deploy multiple web / app servers."""
    fabtools.require.nginx.server()
    fabtools.require.file(
        source   = util.files('nginx/web'),
        path     = '/etc/nginx/sites-available/web',
        owner    = 'root',
        group    = 'root',
        mode     = '755',
        use_sudo = True)

    fabtools.nginx.disable('default')
    fabtools.nginx.enable('web')
    fabtools.require.service.restarted('nginx')
