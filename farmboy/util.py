# vim: tabstop=4 shiftwidth=4 softtabstop=4
import functools
import os
import sys

import pkg_resources
import yaml


from fabric.api import env
from fabric.utils import puts
from fabric.utils import warn


def files(s):
    """Return file path to a file in shared files path or locally defined.

    Check whether the file exists in the defined path otherwise
    fallback to the one shipped with Farm Boy.
    """
    path = os.path.join(env.get('farmboy_files'), s)
    if os.path.exists(path):
        return path

    # TODO(termie): use pkg_resources or whatnot to get the path to the
    #               files we installed with the package
    path = pkg_resources.resource_filename(__name__, '_files/%s' % s)
    return path

def home(s):
    return os.path.join('/home/%s' % env.get('farmboy_user'), s)


def load_roledefs(path='farmboy.yaml'):
    """Return roledefs from a yaml file.

    Looks first for the 'roledefs' key, otherwise
    assume the roledefs are root elements.
    """
    try:
        doc = yaml.load(open(path))
        return doc.get('roledefs', doc)
    except IOError:
        # log.warn('No file found at %s' % path)
        return {}


def load(key, path='farmboy.yaml'):
    """Return key from a yaml file."""
    try:
        doc = yaml.load(open(path))
        return doc.get(key, None)
    except IOError:
        # log.warn('No file found at %s' % path)
        return None


def update(d, path='farmboy.yaml'):
    """Update various keys in a yaml file."""
    try:
        doc = yaml.load(open(path))
    except IOError:
        doc = {}

    doc.update(d)
    yaml.dump(d,
              stream=open(path, 'w'),
              default_flow_style=False,
              indent=2,
              width=72)


def template_file(source, target, context=None):
    context = context and context or {}
    if not os.path.exists(source):
        source = files(source)

    puts('[local] Templating: %s -> %s' % (source, target))

    template = open(source).read()
    open(target, 'w').write(template % context)


def host(s):
    """Try to get a host out of something like username@ipaddress."""
    return s.split('@')[-1]


# decorator
class requires(object):
    """Throw an error if missing a requirement."""

    def __init__(self, module, package):
        self._module = module
        self._package = package

    def __call__(self, f):
        if self._module not in sys.modules:
            @functools.wraps(f)
            def _requires(*args, **kw):
                raise Exception('This task requires an additional package: '
                                '%s' % (self._package))
            return _requires
        return f
