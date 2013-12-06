import os
import time

try:
  from novaclient.v1_1 import client
except ImportError:
  # We'll warn the user if they try to do anything
  pass

from farmboy import util

from fabric.api import env
from fabric.api import execute
from fabric.api import local
from farmboy.fabric_ import task

env.farmboy_os_username = os.environ.get('OS_USERNAME', '')
env.farmboy_os_password = os.environ.get('OS_PASSWORD', '')
env.farmboy_os_tenant_name = os.environ.get('OS_TENANT_NAME', '')
env.farmboy_os_auth_url = os.environ.get('OS_AUTH_URL', '')

env.farmboy_os_image_id = None  # You'll want ubuntu 13.04
env.farmboy_os_image_user = 'ubuntu'
env.farmboy_os_flavor_id = None  # You probably want m1.small
env.farmboy_os_use_neutron = False
env.farmboy_os_network_id = None  # You probably want 'cloud'
env.farmboy_os_network_name = 'private'  # 'private' unless using Neutron
env.farmboy_os_use_floating_ips = False
env.farmboy_os_floating_ip_pool = None
env.farmboy_os_reservation_id = 'farmboy'
env.farmboy_os_security_group = 'farmboy'
env.farmboy_os_keypair = 'farmboy'
env.farmboy_os_keyfile = 'farmboy.key'
env.farmboy_os_keyfile_public = 'farmboy.key.pub'

DEFAULT_ROLEDEF_FILE = 'farmboy.yaml'
DEFAULT_ROLEDEFS = """util.load_roledefs('%s')""" % DEFAULT_ROLEDEF_FILE
DEFAULT_PREAMBLE = """

# The Openstack utilities can launch your VMs for you using
# `farmboy openstack.build`. This setting tells them how many and which roles
# to use, it will cache their addresses by default into the farmboy.yaml
# file so that we can target them for the rest of our actions.
# POWER TIP: Use `farmboy openstack.refresh` to update the farmboy.yaml
#            file if you've manually changed your instances.
env.farmboy_os_instances = ['proxy', 'apt', 'web', 'web']

# We generally want to use a stock Ubuntu 13.04 cloud image, you'll need
# to figure out the ID of one (or upload it using the dashboard).
# POWER TIP: Or you can use our handy picker! `farmboy openstack.images`
env.farmboy_os_image_id = util.load('farmboy_os_image_id', '%(default_yaml)s')

# We usually use the `m1.small` flavor, if this isn't configured already
# the `farmboy openstack.build` command will prompt you with choices.
# POWER TIP: You can use our handy picker! `farmboy openstack.flavors`
env.farmboy_os_flavor_id = util.load('farmboy_os_flavor_id', '%(default_yaml)s')

# We generally want to use a stock Ubuntu 13.04 cloud image, you'll need
# to figure out the ID of one (or upload it using the dashboard).
# POWER TIP: Or you can use our handy picker!
env.farmboy_os_image_id = util.load('farmboy_os_image_id', '%(default_yaml)s')

# If you are using an Openstack cloud that is using Neutron, you need to
# to do some additional network config.
# POWER TIP: Piccckkkeerrr: `farmboy openstack.networks`
env.farmboy_os_use_neutron = False
if env.farmboy_os_use_neutron:
  env.farmboy_os_network_id = util.load('farmboy_os_network_id',
                                        '%(default_yaml)s')
  env.farmboy_os_network_name = util.load('farmboy_os_network_name',
                                          '%(default_yaml)s')

# If you want to use floating ips by default, you can set this to True
# POWER TIP: This just calls `farmboy openstack.associate_floating_ips` after
#            running the build task, you can call that yourself, too.
env.farmboy_os_use_floating_ips = False

# These are the various Openstack-related configuration options and their
# default values. They should be pretty self explanatory for people who've
# used OpenStack.

# env.farmboy_os_username = os.environ.get('OS_USERNAME', '')
# env.farmboy_os_password = os.environ.get('OS_PASSWORD', '')
# env.farmboy_os_tenant_name = os.environ.get('OS_TENANT_NAME', '')
# env.farmboy_os_auth_url = os.environ.get('OS_AUTH_URL', '')

# env.farmboy_os_image_user = 'ubuntu'
# env.farmboy_os_reservation_id = 'farmboy'
# env.farmboy_os_security_group = 'farmboy'
# env.farmboy_os_keypair = 'farmboy'
# env.farmboy_os_keyfile = 'farmboy.key'
# env.farmboy_os_keyfile_public = 'farmboy.key.pub'


# We're using `python-novaclient` for the built-in OpenStack tools, so if you
# use those you should define the common OpenStack environment variables in
# your shell:
#
#   OS_USERNAME
#   OS_PASSWORD
#   OS_TENANT_NAME
#   OS_AUTH_URL

""" % {'default_yaml': DEFAULT_ROLEDEF_FILE}


@task
def build_keypair():
  if not os.path.exists(env.farmboy_os_keyfile):
    local('ssh-keygen -q -N "" -t rsa -f %s' % env.farmboy_os_keyfile)


@task
@util.requires('novaclient', 'novaclient')
def init():
  """Locally set up basic files for using AWS."""
  fabfile_context = {'roledefs': DEFAULT_ROLEDEFS,
                     'keyfile': repr(env.farmboy_os_keyfile),
                     'preamble': DEFAULT_PREAMBLE}
  util.template_file('farmboy/fabfile.py.template',
                     'fabfile.py',
                     fabfile_context)


@task
@util.requires('novaclient', 'novaclient')
def build():
  """Launch and prepare OpenStack instances to be used by Farm Boy.

  This will ensure that a security group and key pair exist.
  It will also terminate any running instances tagged with `farmboy`.
  """
  if not env.farmboy_os_image_id:
    execute(images)
    env.farmboy_os_image_id = util.load('farmboy_os_image_id')

  if not env.farmboy_os_flavor_id:
    execute(flavors)
    env.farmboy_os_flavor_id = util.load('farmboy_os_flavor_id')

  if env.farmboy_os_use_neutron and not env.farmboy_os_network_id:
    execute(networks)
    env.farmboy_os_network_id = util.load('farmboy_os_network_id')
    env.farmboy_os_network_name = util.load('farmboy_os_network_name')


  conn = client.Client(env.farmboy_os_username,
                       env.farmboy_os_password,
                       env.farmboy_os_tenant_name,
                       env.farmboy_os_auth_url,
                       service_type='compute')

  security_group_name = env.farmboy_os_security_group

  # check for security group
  security_group = None
  security_groups = conn.security_groups.list()
  for group in security_groups:
    if group.name == security_group_name:
      security_group = group

  if not security_group:
    util.puts('[os] Creating security group: %s' % security_group)
    security_group = conn.security_groups.create(
        security_group_name, 'default security group for farmboy')

    rules = [dict(ip_protocol='tcp',
                  from_port='22',
                  to_port='22',
                  cidr='0.0.0.0/0'),
             dict(ip_protocol='tcp',
                  from_port='80',
                  to_port='80',
                  cidr='0.0.0.0/0'),
             dict(ip_protocol='tcp',
                  from_port='8000',
                  to_port='9000',
                  cidr='0.0.0.0/0'),
             dict(ip_protocol='udp',
                  from_port='60000',
                  to_port='61000',
                  cidr='0.0.0.0/0'),
             dict(ip_protocol='tcp',
                  from_port='3142',
                  to_port='3142',
                  cidr='0.0.0.0/0')]

    for rule in rules:
      util.puts('[os]   adding rule: %(ip_protocol)s:%(from_port)s-%(to_port)s'
                ' (%(cidr)s)' % rule)
      conn.security_group_rules.create(parent_group_id=security_group.id,
                                       **rule)

  security_groups = [security_group.name]

  # check for keypair
  keypair = None
  keypairs = conn.keypairs.list()
  for pair in keypairs:
    if pair.name == env.farmboy_os_keypair:
      keypair = pair

  if not keypair:
    execute(build_keypair)
    util.puts('[os] Creating keypair: %s' % env.farmboy_os_keypair)
    public_key = open(env.farmboy_os_keyfile_public).read()

    keypair = conn.keypairs.create(env.farmboy_os_keypair,
                                   public_key=public_key)

  execute(terminate)

  machines = env.farmboy_os_instances


  # launch instances with in security group, with keypair
  util.puts('[os] Starting %d instances' % len(machines))
  # tag the instances with their roles
  for machine in machines:
    params = dict(name='farmboy-%s' % machine,
                  image=env.farmboy_os_image_id,
                  flavor=env.farmboy_os_flavor_id,
                  security_groups=security_groups,
                  key_name=env.farmboy_os_keypair,
                  meta={'farmboy': machine})

    if env.farmboy_os_use_neutron:
      params['nics'] = [{'net-id': env.farmboy_os_network_id}]

    inst = conn.servers.create(**params)
    util.puts('[os]  started server: %s -> %s' % (inst.id, machine))

  execute(refresh, expected=len(machines))
  if env.farmboy_os_use_floating_ips:
    execute(associate_floating_ips)


@task
@util.requires('novaclient', 'novaclient')
def terminate():
  """Terminate running OpenStack instances tagged with `farmboy`."""
  conn = client.Client(env.farmboy_os_username,
                       env.farmboy_os_password,
                       env.farmboy_os_tenant_name,
                       env.farmboy_os_auth_url,
                       service_type='compute')

  # check for instances
  running_instances = conn.servers.list()

  # TODO(termie): we _probably_ want to just terminate them all and start
  #               new ones, is there a use case for keeping them?
  for instance in running_instances:
    if (instance.metadata.get('farmboy')
        and instance.status == 'ACTIVE'
        and getattr(instance, 'OS-EXT-STS:task_state') == None):
      util.puts('[os] Terminating running instance: %s (%s)'
                % (instance.id, instance.metadata['farmboy']))
      instance.stop()
      instance.delete()


@task
@util.requires('novaclient', 'novaclient')
def images(filter=None):
  """List the images available on the server."""
  conn = client.Client(env.farmboy_os_username,
                       env.farmboy_os_password,
                       env.farmboy_os_tenant_name,
                       env.farmboy_os_auth_url,
                       service_type='compute')
  images = conn.images.list()
  for i, image in enumerate(images):
    print '[%d] %s (%s)' % (i, image.name, image.id)

  print
  print 'Choose an image from above, or leave blank to skip.'
  print '(It will be written to %s)' % DEFAULT_ROLEDEF_FILE
  print
  number = raw_input('>>> ')

  if not number:
    return

  selected = images[int(number)]
  o = {'farmboy_os_image_id': str(selected.id)}
  util.update(o, DEFAULT_ROLEDEF_FILE)


@task
@util.requires('novaclient', 'novaclient')
def flavors(filter=None):
  """List the flavors available on the server."""
  conn = client.Client(env.farmboy_os_username,
                       env.farmboy_os_password,
                       env.farmboy_os_tenant_name,
                       env.farmboy_os_auth_url,
                       service_type='compute')
  flavors = conn.flavors.list()
  for i, flavor in enumerate(flavors):
    print '[%d] %s (%s)' % (i, flavor.name, flavor.id)

  print
  print 'Choose an flavor from above, or leave blank to skip.'
  print '(It will be written to %s)' % DEFAULT_ROLEDEF_FILE
  print
  number = raw_input('>>> ')

  if not number:
    return

  selected = flavors[int(number)]
  o = {'farmboy_os_flavor_id': str(selected.id)}
  util.update(o, DEFAULT_ROLEDEF_FILE)


@task
@util.requires('novaclient', 'novaclient')
def networks(filter=None):
  """List the networks available on the server."""
  conn = client.Client(env.farmboy_os_username,
                       env.farmboy_os_password,
                       env.farmboy_os_tenant_name,
                       env.farmboy_os_auth_url,
                       service_type='compute')
  networks = conn.networks.list()
  for i, network in enumerate(networks):
    print '[%d] %s (%s)' % (i, network.label, network.id)

  print
  print 'Choose an network from above, or leave blank to skip.'
  print '(It will be written to %s)' % DEFAULT_ROLEDEF_FILE
  print
  number = raw_input('>>> ')

  if not number:
    return

  selected = networks[int(number)]
  o = {'farmboy_os_network_id': str(selected.id),
       'farmboy_os_network_name': str(selected.label)}
  util.update(o, DEFAULT_ROLEDEF_FILE)


@task
@util.requires('novaclient', 'novaclient')
def floating_ip_pools(filter=None):
  """List the floating ip pools available on the server."""
  conn = client.Client(env.farmboy_os_username,
                       env.farmboy_os_password,
                       env.farmboy_os_tenant_name,
                       env.farmboy_os_auth_url,
                       service_type='compute')

  floating_ip_pools = conn.floating_ip_pools.list()
  for i, pool in enumerate(floating_ip_pools):
    print '[%d] %s (%s)' % (i, pool.name)

  print
  print 'Choose a floating ip pool from above, or leave blank to skip.'
  print '(It will be written to %s)' % DEFAULT_ROLEDEF_FILE
  print
  number = raw_input('>>> ')

  if not number:
    return

  selected = pool[int(number)]
  o = {'farmboy_os_floating_ip_pool': str(selected.name)}
  util.update(o, DEFAULT_ROLEDEF_FILE)


@task
@util.requires('novaclient', 'novaclient')
def refresh(expected=None):
  """Update local cache of IPs for OpenStack instances.

  This will write a `farmboy.yaml` file of the running instances
  on OpenStack tagged with `farmboy` and their associated roles.
  """
  conn = client.Client(env.farmboy_os_username,
                       env.farmboy_os_password,
                       env.farmboy_os_tenant_name,
                       env.farmboy_os_auth_url,
                       service_type='compute')

  if expected:
    expected = int(expected)

  max_tries = 30
  for i in range(max_tries):
    util.puts('[os] Fetching running and pending instances')

    # check for instances
    found_instances = []
    running_instances = conn.servers.list()

    # TODO(termie): we _probably_ want to just terminate them all and start
    #               new ones, is there a use case for keeping them?
    for instance in running_instances:
      if (instance.metadata.get('farmboy')
          and instance.status == 'ACTIVE'
          and getattr(instance, 'OS-EXT-STS:task_state') == None):
        found_instances.append(instance)

    if not expected:
      if found_instances:
        break
      util.puts('[os]   nothing found, retrying in 5 seconds (%d of %d)'
                % (i, max_tries))
    else:
      if found_instances and len(found_instances) == expected:
        break
      util.puts('[os]   found %d, expecting %d, retrying in 5 seconds'
                ' (%d of %d)'
                % (len(found_instances), expected, i, max_tries))

    time.sleep(5)

  if not found_instances or (expected and len(found_instances) != expected):
    raise Exception('Did not find enough running instances.')


  o = {'roledefs': {}}
  for inst in found_instances:
    role = str(inst.metadata['farmboy'])
    ip_address = inst.addresses[env.farmboy_os_network_name][0]['addr']
    util.puts('[os]   found: %s (%s)' % (ip_address, role))
    role_l = o['roledefs'].get(role, [])
    role_l.append(str('%s@%s' % (env.farmboy_os_image_user, ip_address)))

    o['roledefs'][role] = role_l

  util.puts('[os] Dumping roledefs to file: %s' % DEFAULT_ROLEDEF_FILE)
  util.update(o, DEFAULT_ROLEDEF_FILE)


@task
@util.requires('novaclient', 'novaclient')
def associate_floating_ips():
  """Ensure there are enough floating ips and associate them with instances."""
  conn = client.Client(env.farmboy_os_username,
                       env.farmboy_os_password,
                       env.farmboy_os_tenant_name,
                       env.farmboy_os_auth_url,
                       service_type='compute')

  util.puts('[os] Ensuring instances have floating ips associated.')

  # Get our running instances
  found_instances = []
  running_instances = conn.servers.list()

  for instance in running_instances:
    if (instance.metadata.get('farmboy')
        and instance.status == 'ACTIVE'
        and getattr(instance, 'OS-EXT-STS:task_state') == None):
      found_instances.append(instance)

  instances_needing_ips = dict((inst.id, inst) for inst in found_instances)
  available_ips = {}
  instance_ips = {}

  floating_ips = conn.floating_ips.list()

  # figure out how many we need and how many we have available
  for i, floating_ip in enumerate(floating_ips):
    if floating_ip.instance_id in instances_needing_ips:
      instances_needing_ips.pop(floating_ip.instance_id)
      instance_ips[floating_ip.instance_id] = floating_ip.ip
    elif not floating_ip.instance_id:
      available_ips[floating_ip.id] = floating_ip

  # do we need more?
  needed_ips = len(instances_needing_ips) - len(available_ips)

  # stupid floating ip pool tricks
  if needed_ips > 0:
    util.puts('[os] Creating %d more floating ips' % needed_ips)
    if env.farmboy_os_floating_ip_pool:
      pool = env.farmboy_os_floating_ip_pool
    else:
      # If we have more than one pool, launch _another_ picker
      pools = conn.floating_ip_pools.list()
      if len(pools) == 1:
        pool = pools[0].name
        env.farmboy_os_floating_ip_pool = pool
        util.update({'farmboy_os_floating_ip_pool': str(pool)})
      else:
        execute(floating_ip_pools)
        pool = util.load('farmboy_os_floating_ip_pool')

    # make all the ips we need
    for i in range(needed_ips):
      m = conn.floating_ips.create(pool=pool)
      util.puts('[os]   created: %s (%s)' % (m.ip, m.id))
      available_ips = [m.id] = m

  util.puts('[os] Associating floating IPs with instances.')
  for inst_id, inst in instances_needing_ips.iteritems():
    next_ip_id, next_ip = available_ips.popitem()
    inst.add_floating_ip(next_ip.ip)
    util.puts('[os]   associated: %s -> %s' % (next_ip.ip, inst.id))

    instance_ips[inst_id] = next_ip.ip

  # By now we should have IPs for everything, let's update the roledefs
  o = {'roledefs': {}}
  for inst in found_instances:
    role = str(inst.metadata['farmboy'])
    ip_address = instance_ips[inst.id]
    util.puts('[os]   found: %s (%s)' % (ip_address, role))
    role_l = o['roledefs'].get(role, [])
    role_l.append(str('%s@%s' % (env.farmboy_os_image_user, ip_address)))

    o['roledefs'][role] = role_l

  util.puts('[os] Dumping roledefs to file: %s' % DEFAULT_ROLEDEF_FILE)
  util.update(o, DEFAULT_ROLEDEF_FILE)

