# vim: tabstop=4 shiftwidth=4 softtabstop=4
import fabtools.files
import fabtools.require


from fabric.api import execute
from fabric.api import parallel
from fabric.api import roles
from fabric.api import sudo
from fabric.api import task


@roles('web')
@task
def deploy():
    """Add gunicorn to the <web> hosts."""
    fabtools.require.deb.packages([
        'gunicorn'
    ])
    restart()


#@roles('web')
#@task
def restart():
    """Gunicorn doesn't act super swell, so look for a PID."""
    if fabtools.files.is_file('/var/run/gunicorn/django.pid'):
        sudo('service gunicorn restart', pty=False)
    else:
        #fabtools.service.start('gunicorn')
        sudo('service gunicorn start', pty=False)
