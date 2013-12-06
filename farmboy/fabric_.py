
"""Overrides to a couple features in Fabric."""

from fabric import decorators
from fabric import tasks
from fabric.api import env


env.skip_missing_roles = True


# Copied from https://github.com/fabric/fabric with a small change to
# use our class instead of the default
def task(*args, **kwargs):
    """
    Decorator declaring the wrapped function to be a new-style task.

    May be invoked as a simple, argument-less decorator (i.e. ``@task``) or
    with arguments customizing its behavior (e.g. ``@task(alias='myalias')``).

    Please see the :ref:`new-style task <task-decorator>` documentation for
    details on how to use this decorator.

    .. versionchanged:: 1.2
        Added the ``alias``, ``aliases``, ``task_class`` and ``default``
        keyword arguments. See :ref:`task-decorator-arguments` for details.
    .. versionchanged:: 1.5
        Added the ``name`` keyword argument.

    .. seealso:: `~fabric.docs.unwrap_tasks`, `~fabric.tasks.WrappedCallableTask`
    """
    invoked = bool(not args or kwargs)
    task_class = kwargs.pop("task_class", AdvancedRolesTask)
    if not invoked:
        func, args = args[0], ()

    def wrapper(func):
        return task_class(func, *args, **kwargs)

    return wrapper if invoked else wrapper(func)


def build_real_roles(roles):
  all_roles = env.roledefs.keys()

  out_roles = set()

  # Special role that resolves to all defined hosts.
  if 'all' in roles:
    out_roles.update(all_roles)

  for role in roles:
    if role == 'all':
      continue

    if role.startswith('+'):
      out_roles.add(role[1:])
    elif role.startswith('-'):
      out_roles.discard(role[1:])
    else:
      # If we skip missing check whether this role is defined first
      if env.skip_missing_roles:
        if role in all_roles:
          out_roles.add(role)
      else:
        out_roles.add(role)

  return list(out_roles)


class AdvancedRolesTask(tasks.WrappedCallableTask):
  """Task that adds some additional features to roles.

  Allows:
    Prepending a role with '+' to require include.
    Prepending a role with a '-' to force exclude.
    A special role 'all' that resolves to all the roles.
    By default skips roles that are missing.
  """

  def get_hosts(self, *args, **kw):
    roles = build_real_roles(getattr(self, 'roles', []))
    setattr(self, 'roles', roles)
    return super(AdvancedRolesTask, self).get_hosts(*args, **kw)

