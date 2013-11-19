import time

try:
  import boto.exception
  from boto import ec2
except ImportError:
  # We'll warn the user if they try to do anything
  pass

import yaml

from farmboy import util

from fabric.api import env
from fabric.api import execute
from fabric.api import task


env.farmboy_aws_region = 'us-west-2'
env.farmboy_aws_security_group = 'farmboy'
env.farmboy_aws_key_pair = 'farmboy'
env.farmboy_aws_image_id = 'ami-1e0c902e' #us-west-2 raring amd64
env.farmboy_aws_image_user = 'ubuntu'


DEFAULT_ROLEDEF_FILE = 'farmboy.aws.yaml'
DEFAULT_KEYFILE = 'farmboy.pem'
DEFAULT_ROLEDEFS = """util.load_roledefs('%s')""" % DEFAULT_ROLEDEF_FILE
DEFAULT_PREAMBLE = """

# The AWS utilities can launch your VMs for you using `farmboy aws.build`.
# This setting tells them how many and which roles to use, it will cache
# their addresses by default into the farmboy.aws.yaml file so that we
# can target them for the rest of our actions.
# POWER TIP: Use `farmboy aws.refresh` to update the farmboy.aws.yaml
#            file if you've manually changed your instances on EC2.
env.farmboy_aws_instances = ['proxy', 'apt', 'web', 'web']

# These are the various AWS-related configuration options and their default
# values. They should be pretty self explanatory for people who've used AWS.

# env.farmboy_aws_region = %(region)s
# env.farmboy_aws_security_group = %(security_group)s
# env.farmboy_aws_key_pair = %(key_pair)s
# env.farmboy_aws_image_id = %(image_id)s  # us-west-2 raring amd64
# env.farmboy_aws_image_user = %(image_user)s

# We're using `boto` for the built-in EC2 tools, so if you use those
# you should define the common AWS environment variables in your shell:
#
#   AWS_ACCESS_KEY_ID
#   AWS_SECRET_ACCESS_KEY

""" % {'region': repr(env.farmboy_aws_region),
       'security_group': repr(env.farmboy_aws_security_group),
       'key_pair': repr(env.farmboy_aws_key_pair),
       'image_id': repr(env.farmboy_aws_image_id),
       'image_user': repr(env.farmboy_aws_image_user)}


@task
@util.requires('boto', 'boto')
def init():
  """Locally set up basic files for using AWS."""
  fabfile_context = {'roledefs': DEFAULT_ROLEDEFS,
                     'keyfile': repr('%s.pem' % env.farmboy_aws_key_pair),
                     'preamble': DEFAULT_PREAMBLE}
  util.template_file('farmboy/fabfile.py.template',
                     'fabfile.py',
                     fabfile_context)


@task
@util.requires('boto', 'boto')
def build():
  """Launch and prepare AWS instances to be used by Farm Boy.

  This will ensure that a security group and key pair exist.
  It will also terminate any running instances tagged with `farmboy`.
  """
  conn = ec2.connect_to_region(env.farmboy_aws_region)
  security_group = env.farmboy_aws_security_group

  # check for security group
  try:
    security_groups = conn.get_all_security_groups([security_group])
  except boto.exception.EC2ResponseError:
    security_groups = []

  if not security_groups:
    util.puts('[aws] Creating security group: %s' % security_group)
    security_group = conn.create_security_group(
        security_group, 'default security group for farmboy')

    rules = [dict(ip_protocol='tcp',
                  from_port='22',
                  to_port='22',
                  cidr_ip='0.0.0.0/0'),
             dict(ip_protocol='tcp',
                  from_port='80',
                  to_port='80',
                  cidr_ip='0.0.0.0/0'),
             dict(ip_protocol='tcp',
                  from_port='8000',
                  to_port='9000',
                  cidr_ip='0.0.0.0/0'),
             dict(ip_protocol='udp',
                  from_port='60000',
                  to_port='61000',
                  cidr_ip='0.0.0.0/0'),
             dict(ip_protocol='tcp',
                  from_port='3142',
                  to_port='3142',
                  cidr_ip='0.0.0.0/0')]

    for rule in rules:
      util.puts('[aws]   adding rule: %(ip_protocol)s:%(from_port)s-%(to_port)s'
                ' (%(cidr_ip)s)' % rule)
      security_group.authorize(**rule)


  security_groups = [security_group]

  # check for keypair
  key_pair = conn.get_key_pair(env.farmboy_aws_key_pair)
  if not key_pair:
    util.puts('[aws] Creating key pair: %s' % env.farmboy_aws_key_pair)
    key_pair = conn.create_key_pair(env.farmboy_aws_key_pair)
    key_pair.save('./')

  execute(terminate)

  machines = env.farmboy_aws_instances

  # launch instances with in security group, with keypair
  util.puts('[aws] Starting %d instances' % len(machines))
  reservation = conn.run_instances(image_id=env.farmboy_aws_image_id,
                                   min_count=len(machines),
                                   max_count=len(machines),
                                   key_name=env.farmboy_aws_key_pair,
                                   security_groups=security_groups)

  # get instances for returned reservation
  new_instances = reservation.instances[:]

  # tag the instances with their roles
  for machine in machines:
    inst = new_instances.pop()
    util.puts('[aws]   assigning role: %s -> %s' % (inst.id, machine))
    inst.add_tag('farmboy', machine)

  execute(refresh, expected=len(machines))


@task
@util.requires('boto', 'boto')
def terminate():
  """Terminate running AWS instances tagged with `farmboy`."""
  conn = ec2.connect_to_region(env.farmboy_aws_region)
  # check for instances
  running_instances = conn.get_only_instances(
      filters={'tag-key': 'farmboy',
               'instance-state-name': 'pending',
               'instance-state-name': 'running'})

  # TODO(termie): we _probably_ want to just terminate them all and start
  #               new ones, is there a use case for keeping them?
  for instance in running_instances:
    util.puts('[aws] Terminating running instance: %s (%s)'
              % (instance.id, instance.tags['farmboy']))
    instance.terminate()


@task
@util.requires('boto', 'boto')
def refresh(expected=None):
  """Update local cache of IPs for AWS instances.

  This will write a `farmboy.aws.yaml` file of the running instances
  on AWS tagged with `farmboy` and their associated roles.
  """
  conn = ec2.connect_to_region(env.farmboy_aws_region)

  max_tries = 15
  for i in range(max_tries):
    util.puts('[aws] Fetching running and pending instances')
    running_instances = conn.get_only_instances(
        filters={'tag-key': 'farmboy',
                 'instance-state-name': 'pending',
                 'instance-state-name': 'running'})

    if not expected:
      if running_instances:
        break
      util.puts('[aws]   nothing found, retrying in 5 seconds (%d of %d)'
                % (i, max_tries))
    else:
      if running_instances and len(running_instances) == expected:
        break
      util.puts('[aws]   found %d, expecting %d, retrying in 5 seconds'
                ' (%d of %d)'
                % (len(running_instances), expected, i, max_tries))

    time.sleep(5)

  if not running_instances or (expected and len(running_instances) != expected):
    raise Exception('Did not find enough running instances.')


  o = {'roledefs': {}}
  for inst in running_instances:
    role = str(inst.tags['farmboy'])
    util.puts('[aws]   found: %s (%s)' % (inst.ip_address, role))
    role_l = o['roledefs'].get(role, [])
    role_l.append(str('%s@%s' % (env.farmboy_aws_image_user, inst.ip_address)))

    o['roledefs'][role] = role_l

  util.puts('[aws] Dumping roledefs to file: %s' % DEFAULT_ROLEDEF_FILE)
  yaml.dump(o,
            stream=open(DEFAULT_ROLEDEF_FILE, 'w'),
            default_flow_style=False,
            indent=2,
            width=72)

