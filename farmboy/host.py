
"""Host config as classes.

When we are defining which instances we want to instantiate, the syntax
should be something like:

  instances = [host.Web(), host.Web(), host.Proxy() + host.Apt()]

This should result, at the build step, in:

  3 instances being launched
  4 roles being assigned
  Security group rules allowing access to ports:
    80 and 22 on the two web hosts
    80 (proxy) and 3142 (apt) on the proxy+apt host

Our goal is to make the simplest interface for configuring a few hosts.
Ideally the defaults should support 85% of most use cases without additional
configuration, and diving deeper should support the other 14%.

For the moment the main point of having hosts defined in code is so that we
can build our list of security group rules based on which ports hosts need
opened.

For example, while web hosts will predictably want ports 80 to be
accessible, whether we want port 3306 or 5432 open on the database server
depends on whether we are installying MySQL vs Postgres. A common pattern
for supporting this would be:

  from farmboy import host
  from farmboy import postgres
  instances = [host.Web(), postgres.DbHost()]

The postgres.DbHost in this case, would have the role 'db', but have the
default Postgres port included in the security group rules it would like
defined.

In order to support composability of hosts, like in the example above where
a single host is both the proxy and the apt cache, Host objects support an
overloaded addition operator to combine configs to produce a new config. The
operation tries to do the right thing with regards to appending vs overriding
values, so far there aren't any conflicts.
"""



class _ListWrapper(list):
  """Exists just to add the 'inherit' property."""
  pass


class _SetWrapper(set):
  """Exists just to add the 'inherit' property."""
  pass


class hashabledict(dict):
  def __hash__(self):
    return hash(tuple(sorted(self.items())))


class SgRule(hashabledict):
  pass


SSH_ACCESS = SgRule({'ip_protocol': 'tcp',
                     'from_port': '22',
                     'to_port': '22',
                     'cidr': '0.0.0.0/0'})


def inherit(prop):
  if type(prop) is type([]):
    prop = _ListWrapper(prop)

  if type(prop) is type(set()):
    prop = _SetWrapper(prop)

  prop.inherit = True
  return prop


class _InheritableAttributes(type):
  def __new__(cls, class_name, class_parents, class_attrs):
    attrs = {}
    for k, v in class_attrs.iteritems():
      if getattr(v, 'inherit', False):
        # NOTE(termie): we're a wrapped class because set uses __slots__
        #if type(v) == type([]):
        if hasattr(v, 'add'):
          l = v
          for p in class_parents:
            l = l | getattr(p, k, [])
          attrs[k] = l
        # NOTE(termie): we're a wrapped class because set uses __slots__
        #if type(v) == type([]):
        if hasattr(v, 'append'):
          l = v
          for p in class_parents:
            l = l + getattr(p, k, [])
          attrs[k] = l
      else:
        attrs[k] = v
    return type.__new__(cls, class_name, class_parents, attrs)


class Host(dict):
  """Generic host base class."""
  __metaclass__ = _InheritableAttributes

  sg_rules = {SSH_ACCESS}

  def __init__(self, *args, **kw):
    super(Host, self).__init__(*args, **kw)
    properties = dict((k, getattr(self, k)) for k in dir(self)
                      if k not in dir(dict) and k[0] != '_')
    properties.update(self)
    self.update(properties)

  def __add__(self, other):
    """Create a new host config by combining with another.

    This will basically just call the + operator on any augmented property
    to let it handle combining, otherwise it will overwrite the value with
    the new value.
    """
    o = dict(self.iteritems())
    for name, prop in other.iteritems():
      #print name
      #print prop
      #print self[name]
      if name in self and hasattr(self[name], 'add'):
        o[name] = self[name] | prop
      elif name in self and hasattr(self[name], 'appemd'):
        o[name] = self[name] + prop
      else:
        o[name] = prop

    return Host(**o)


class Web(Host):
  roles = {'web'}

  sg_rules = {SgRule({'ip_protocol': 'tcp',
                      'from_port': '80',
                      'to_port': '80',
                      'cidr': '0.0.0.0/0'})}
  sg_rules = inherit(sg_rules)


class Proxy(Host):
  roles = {'proxy'}
  sg_rules = {SgRule({'ip_protocol': 'tcp',
                      'from_port': '80',
                      'to_port': '80',
                      'cidr': '0.0.0.0/0'})}
  sg_rules = inherit(sg_rules)


class Apt(Host):
  roles = {'apt'}
  sg_rules = {SgRule({'ip_protocol': 'tcp',
                      'from_port': '3142',
                      'to_port': '3142',
                      'cidr': '0.0.0.0/0'})}
  sg_rules = inherit(sg_rules)


if __name__ == '__main__':
  w = Web(name='web1')
  a = Apt(name='apt')
  p = Proxy()
  ap = a + p

  import pprint
  print 'w\n', pprint.pformat(w.items())
  print 'a\n', pprint.pformat(a.items())
  print 'p\n', pprint.pformat(p.items())
  print 'ap\n', pprint.pformat(ap.items())
