from fabric.api import env
from fabric.api import parallel
from fabric.api import roles
from farmboy.fabric_ import task
import fabtools.require

from farmboy import util


def _current_role():
  hs = env.host_string
  for role, hosts in env.roledefs.iteritems():
    if hs in hosts:
      return role


@task
@roles('all')
@parallel
def hosts():
  current_role = _current_role()
  hostsfile = util.files('farmboy/hosts')
  hosts = []
  hosts.append('127.0.0.1 localhost farmboy-%s' % current_role)
  # TODO(termie): does this break if we use callable roledefs?
  for role, role_hosts in env.roledefs.iteritems():
    if len(role_hosts) == 1:
      if role == current_role:
        continue

      hosts.append('%s farmboy-%s' % (util.host(role_hosts[0]), role))
      continue

    for i, role_host in enumerate(role_hosts):
      hosts.append('%s farmboy-%s-%s' % (util.host(role_host), role, i))

  hosts_str = '\n'.join(hosts)

  fabtools.require.files.template_file(
      template_source = hostsfile,
      context  = {'hosts': hosts_str},
      path     = '/etc/hosts',
      owner    = 'root',
      group    = 'root',
      mode     = '644',
      use_sudo = True)
