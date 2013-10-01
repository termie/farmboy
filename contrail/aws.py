
import yaml

from fabric.api import execute
from fabric.api import task
from boto import ec2
import boto.exception

REGION='us-west-2'
SECURITY_GROUP='contrail'
KEY_PAIR='contrail'
AMI='ami-1e0c902e' #us-west-2 raring amd64




def create_security_group():
  pass





@task
def build():
  conn = ec2.connect_to_region(REGION)

  # check for security group
  try:
    security_groups = conn.get_all_security_groups([SECURITY_GROUP])
  except boto.exception.EC2ResponseError:
    security_groups = []

  if not security_groups:
    security_group = conn.create_security_group(
        SECURITY_GROUP, 'default security group for contrail')
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

  security_groups = [SECURITY_GROUP]

  # check for keypair
  key_pair = conn.get_key_pair(KEY_PAIR)
  if not key_pair:
    key_pair = conn.create_key_pair(KEY_PAIR)
    key_pair.save('./')

  # check for instances
  running_instances = conn.get_only_instances(
      filters={'tag-key': 'contrail',
               'instance-state-name': 'running'})

  # TODO(termie): we _probably_ want to just terminate them all and start
  #               new ones, is there a use case for keeping them?
  for instance in running_instances:
    instance.terminate()

  machines = ['proxy', 'apt', 'web', 'web']

  # launch instances with in security group, with keypair
  reservation = conn.run_instances(image_id=AMI,
                                   min_count=len(machines),
                                   max_count=len(machines),
                                   key_name=KEY_PAIR,
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
  conn = ec2.connect_to_region(REGION)
  running_instances = conn.get_only_instances(
      filters={'tag-key': 'contrail',
               'instance-state-name': 'pending',
               'instance-state-name': 'running'})

  o = {'roledefs': {}}
  for inst in running_instances:
    role = str(inst.tags['contrail'])
    role_l = o['roledefs'].get(role, [])
    role_l.append(str('ubuntu@%s' % inst.ip_address))

    o['roledefs'][role] = role_l

  yaml.dump(o,
            stream=open('contrail.aws.yaml', 'w'),
            default_flow_style=False,
            indent=2,
            width=72)

