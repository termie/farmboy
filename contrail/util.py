# vim: tabstop=4 shiftwidth=4 softtabstop=4
import os

from fabric.api import env
import yaml


def files(s):
    return os.path.join(env.get('contrail_files'), s)


def home(s):
    return os.path.join('/home/%s' % env.get('contrail_user'), s)


def load_roledefs(path='contrail.yaml'):
    """Return roledefs from a yaml file.

    Looks first for the 'roledefs' key, otherwise
    assume the roledefs are root elements.
    """
    doc = yaml.load(open(path))
    return doc.get('roledefs', doc)
