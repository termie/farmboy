# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os

from farmboy import aptcacher
from farmboy import aws
from farmboy import core
from farmboy import django
from farmboy import files
from farmboy import gitlab
from farmboy import gunicorn
from farmboy import haproxy
from farmboy import jenkins
from farmboy import openstack
from farmboy import nginx
from farmboy import tomcat
from farmboy import util
from farmboy import vagrant


from fabric.api import env
from fabric.api import execute
from fabric.api import task
