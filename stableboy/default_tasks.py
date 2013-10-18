# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os

from stableboy import aptcacher
from stableboy import aws
from stableboy import core
from stableboy import django
from stableboy import gitlab
from stableboy import gunicorn
from stableboy import haproxy
from stableboy import jenkins
from stableboy import nginx
from stableboy import tomcat
from stableboy import util
from stableboy import vagrant


from fabric.api import env
from fabric.api import execute
from fabric.api import task
