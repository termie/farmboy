# vim: tabstop=4 shiftwidth=4 softtabstop=4
import fabtools.require

from fabric.api import env
from fabric.api import parallel
from fabric.api import roles
from fabric.api import settings
from farmboy.fabric_ import task

from farmboy import util


env.farmboy_mysql_password = None


def _generate_password():
    # Chosen at random
    new_password = 'secret'
    return new_password


@task
@roles('db')
@parallel
def deploy():
    """Add mysql to the db hosts."""
    # If we don't have a key yet generate one and save it locally
    if not env.farmboy_mysql_password:
        new_password = _generate_password()
        util.update({'farmboy_mysql_password': new_password})
        env.farmboy_mysql_password = new_password

    mysql_password = env.farmboy_mysql_password

    fabtools.require.mysql.server(password=mysql_password)


@task
@roles('db')
def create_user(name, password=None, host=None):
    if not password:
        password = util.load('farmboy_mysql_password_%s' % name)

    if not password:
        password = _generate_password()
        util.update({'farmboy_mysql_password_%s' % name: password})

    with settings(mysql_user='root', mysql_password=env.farmboy_mysql_password):
        fabtools.require.mysql.user(name, password, host=host)


@task
@roles('db')
def create_database(name, owner=None, owner_host=None, **kw):
    with settings(mysql_user='root', mysql_password=env.farmboy_mysql_password):
        fabtools.require.mysql.database(
                name, owner=owner, owner_host=owner_host, **kw)


