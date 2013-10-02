
import boto.exception
from boto import ec2
import yaml

from contrail import util

from fabric.api import env
from fabric.api import execute
from fabric.api import task


env.contrail_aws_region = 'us-west-2'
env.contrail_aws_security_group = 'contrail'
env.contrail_aws_key_pair = 'contrail'
env.contrail_aws_image_id = 'ami-1e0c902e' #us-west-2 raring amd64
env.contrail_aws_image_user = 'ubuntu'


DEFAULT_ROLEDEF_FILE = 'contrail.aws.yaml'
DEFAULT_KEYFILE = 'contrail.pem'
DEFAULT_ROLEDEFS = """util.load_roledefs('%s')""" % DEFAULT_ROLEDEF_FILE
DEFAULT_PREAMBLE = """

# The AWS utilities can launch your VMs for you using `contrail aws.build`.
# This setting tells them how many and which roles to use, it will cache
# their addresses by default into the contrail.aws.yaml file so that we
# can target them for the rest of our actions.
# POWER TIP: Use `contrail aws.refresh` to update the contrail.aws.yaml
#            file if you've manually changed your instances on EC2.
env.contrail_aws_instances = ['proxy', 'apt', 'web', 'web']

# These are the various AWS-related configuration options and their default
# values. They should be pretty self explanatory for people who've used AWS.

# env.contrail_aws_region = %(region)s
# env.contrail_aws_security_group = %(security_group)s
# env.contrail_aws_key_pair = %(key_pair)s
# env.contrail_aws_image_id = %(image_id)s  # us-west-2 raring amd64
# env.contrail_aws_image_user = %(image_user)s

# We're using `boto` for the built-in EC2 tools, so if you use those
# you should define the common AWS environment variables in your shell:
#
#   AWS_ACCESS_KEY_ID
#   AWS_SECRET_ACCESS_KEY

""" % {'region': repr(env.contrail_aws_region),
       'security_group': repr(env.contrail_aws_security_group),
       'key_pair': repr(env.contrail_aws_key_pair),
       'image_id': repr(env.contrail_aws_image_id),
       'image_user': repr(env.contrail_aws_image_user)}


@task
def init():
  fabfile_context = {'roledefs': DEFAULT_ROLEDEFS,
                     'keyfile': repr(DEFAULT_KEYFILE),
                     'preamble': DEFAULT_PREAMBLE}
  util.template_file('contrail/fabfile.py', 'fabfile.py', fabfile_context)


@task
def build():
  conn = ec2.connect_to_region(env.contrail_aws_region)
  security_group = env.contrail_aws_security_group

  # check for security group
  try:
    security_groups = conn.get_all_security_groups([security_group])
  except boto.exception.EC2ResponseError:
    security_groups = []

  if not security_groups:
    security_group = conn.create_security_group(
        security_group, 'default security group for contrail')
    security_group.authorize(ip_protocol='tcp',
                             from_port='22',
                             to_port='22',
                             cidr_ip='0.0.0.0/0')
    security_group.authorize(ip_protocol='tcp',
                             from_port='80',
                             to_port='80',
                             cidr_ip='0.0.0.0/0')
    security_group.authorize(ip_protocol='tcp',
                             from_port='8000',
                             to_port='9000',
                             cidr_ip='0.0.0.0/0')
    security_group.authorize(ip_protocol='udp',
                             from_port='60000',
                             to_port='61000',
                             cidr_ip='0.0.0.0/0')

  security_groups = [security_group]

  # check for keypair
  key_pair = conn.get_key_pair(env.contrail_aws_key_pair)
  if not key_pair:
    key_pair = conn.create_key_pair(env.contrail_aws_key_pair)
    key_pair.save('./')

  # check for instances
  running_instances = conn.get_only_instances(
      filters={'tag-key': 'contrail',
               'instance-state-name': 'running'})

  # TODO(termie): we _probably_ want to just terminate them all and start
  #               new ones, is there a use case for keeping them?
  for instance in running_instances:
    instance.terminate()

  machines = env.contrail_aws_instances

  # launch instances with in security group, with keypair
  reservation = conn.run_instances(image_id=env.contrail_aws_image_id,
                                   min_count=len(machines),
                                   max_count=len(machines),
                                   key_name=env.contrail_aws_key_pair,
                                   security_groups=security_groups)

  # get instances for returned reservation
  new_instances = reservation.instances[:]

  # tag the instances with their roles
  for machine in machines:
    inst = new_instances.pop()
    inst.add_tag('contrail', machine)

  execute(refresh)


@task
def refresh():
  """Query AWS and dump the IPs we care about to a yaml file."""
  conn = ec2.connect_to_region(env.contrail_aws_region)
  running_instances = conn.get_only_instances(
      filters={'tag-key': 'contrail',
               'instance-state-name': 'pending',
               'instance-state-name': 'running'})

  o = {'roledefs': {}}
  for inst in running_instances:
    role = str(inst.tags['contrail'])
    role_l = o['roledefs'].get(role, [])
    role_l.append(str('%s@%s' % (env.contrail_aws_image_user, inst.ip_address)))

    o['roledefs'][role] = role_l

  yaml.dump(o,
            stream=open(DEFAULT_ROLEDEF_FILE, 'w'),
            default_flow_style=False,
            indent=2,
            width=72)

