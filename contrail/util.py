# vim: tabstop=4 shiftwidth=4 softtabstop=4
import os

from fabric.api import env


def files(s):
    return os.path.join(env.get('contrail_files'), s)


def home(s):
    return os.path.join('/home/%s' % env.get('contrail_user'), s)

