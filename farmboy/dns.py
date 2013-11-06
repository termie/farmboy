from fabric.api import env
from fabric.api import parallel
from fabric.api import roles
from fabric.api import task
import fabtools.require

from farmboy import util

@roles('apt', 'ci', 'proxy', 'vcs', 'web')
@task
@parallel
def hosts():
  hostsfile = util.files('farmboy/hosts')
  hosts = []
  # TODO(termie): does this break if we use callable roledefs?
  for role, role_hosts in env.roledefs.iteritems():
    if len(role_hosts) == 1:
      hosts.append('%s %s' % (util.host(role_hosts[0]), role))
      continue

    for i, role_host in enumerate(role_hosts):
      hosts.append('%s %s-%s' % (util.host(role_host), role, i))

  hosts_str = '\n'.join(hosts)
  print hosts_str

  fabtools.require.files.template_file(
      template_source = hostsfile,
      context  = {'hosts': hosts_str},
      path     = '/etc/hosts',
      owner    = 'root',
      group    = 'root',
      mode     = '644',
      use_sudo = True)
