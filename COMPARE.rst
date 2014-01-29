

Ansible
-------

Inventory file, basic INI format with sections denoting groups.
  Wildcard syntax to define many hosts at once.
  Hosts are just hostnames with optional keyword arguments.
  Group variables definable per group.
  Groups of groups.
  Subdirectory structure of YAML files for defining group and host variables.
Dynamic inventory information based on Cobbler.
Playbooks are YAML syntax, also.


CFEngine
--------

Custom configuration language, based on state shifts.

If you already like CFEngine, nothing is going to change your mind.


Chef
----

Config broken into multiple levels:

  Environments define a wide context, like Production, Staging, etc.
  Roles are compositable and applied m2m to hosts via an intermediate lookup
    to discover which roles a given host should have.
    Roles are defined via a ruby-dsl or json that evaluates to a dict.
  Attributes are overridable at any point in the stack, and are provided by
    a separate agent, Ohai, to give basic host information.


Heat
----

Templates are very verbose YAML files.
  Pretty much runs shell commands.
  Non-arbitrary constraints.
  Writes output variables to a common location.


SaltStack
---------

Config file is YAML, based on state declarations.
  Sub-config files can be used to define roles.

Task definition defined via config file as well.
  YAML files get templated using Jinja to save time writing YAML files.
  YAML files can call additional Salt functions.

Environment config via base YAML file.

Pillar tool, apparently correlating these configs.
