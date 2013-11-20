import errno
import os

import pkg_resources

from fabric.api import env
from fabric.api import local
from fabric.api import puts
from fabric.api import task


def _makedir(p):
  try:
    os.mkdir(p)
    puts('[files] Making directory: %s' % p)
  except OSError as exc:
      if exc.errno == errno.EEXIST and os.path.isdir(p):
          pass



@task
def init(force=False):
  """Copy the template files to the local directory for easy modification."""

  #_makedir(env.get('farmboy_files'))
  _makedir('./files')

  top_level = pkg_resources.resource_listdir(__name__, '_files')
  for path in top_level:
    if not pkg_resources.resource_isdir(__name__, '_files/%s' % path):
      continue

    _makedir('./files/%s' % path)

    for sub in pkg_resources.resource_listdir(__name__, '_files/%s' % path):
      new_path = './files/%s/%s' % (path, sub)
      if not force and os.path.exists(new_path):
        continue

      old_path = pkg_resources.resource_filename(__name__,
                                                 '_files/%s/%s' % (path, sub))

      local('cp %s %s' % (old_path, new_path))
