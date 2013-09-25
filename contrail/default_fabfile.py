# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os

from contrail import aptcacher
from contrail import core
from contrail import django
from contrail import gitlab
from contrail import gunicorn
from contrail import haproxy
from contrail import jenkins
from contrail import nginx
from contrail import tomcat
from contrail import util
from contrail import vagrant


from fabric.api import env
from fabric.api import execute
from fabric.api import task
