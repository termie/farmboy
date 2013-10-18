# vim: tabstop=4 shiftwidth=4 softtabstop=4
import os

import fabtools.files
import fabtools.require

from farmboy import util


from fabric.api import env
from fabric.api import execute
from fabric.api import parallel
from fabric.api import put
from fabric.api import roles
from fabric.api import sudo
from fabric.api import task

from farmboy import gunicorn


@roles('web')
@task
@parallel
def deploy(path=None, use_gunicorn=True):
    """Put a django site onto the web servers."""
    if path is None:
        path = env.farmboy_django_app

    fabtools.require.python.package('django', use_sudo=True)

    project = os.path.basename(path)
    fabtools.require.directory(
            path = util.home('www'),
            owner = env.farmboy_user,
            group = env.farmboy_user,
            use_sudo = True)

    put(local_path = path,
        remote_path = util.home('www'),
        use_sudo = True)

    sudo('chown -R %s:%s /home/%s/www/%s' % (env.farmboy_user,
                                             env.farmboy_user,
                                             env.farmboy_user,
                                             project))

    if use_gunicorn:
        fabtools.require.files.template_file(
            template_source = util.files('gunicorn/django'),
            path     = '/etc/gunicorn.d/django',
            context  = {'project': project},
            owner    = 'root',
            group    = 'root',
            mode     = '644',
            use_sudo = True)

        gunicorn.restart()
