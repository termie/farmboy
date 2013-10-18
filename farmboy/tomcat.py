# vim: tabstop=4 shiftwidth=4 softtabstop=4
import fabtools.nginx
import fabtools.require

from fabric.api import parallel
from fabric.api import roles
from fabric.api import task


@roles('web')
@task
@parallel
def deploy():
    """Add tomcat to the <web> hosts."""
    fabtools.require.deb.packages([
        'tomcat7'
    ])
