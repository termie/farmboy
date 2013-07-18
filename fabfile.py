# vim: tabstop=4 shiftwidth=4 softtabstop=4

from contrail import core
from contrail import django
from contrail import haproxy
from contrail import gunicorn
from contrail import nginx
from contrail import tomcat
from contrail import vagrant


from fabric.api import execute
from fabric.api import task


@task(default=True)
def demo():
    #execute(core.install_user)
    execute(haproxy.deploy)
    execute(nginx.deploy)
    execute(gunicorn.deploy)
    execute(django.deploy)
