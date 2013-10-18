"""Simple directory watching tool to trigger farmboy commands."""

import argparse
import os
import re
import stat
import subprocess
import sys
import threading
import time

from watchdog import events
from watchdog.observers import api
from watchdog.observers import polling
from watchdog.utils import dirsnapshot


from watchdog.events import\
  DirMovedEvent,\
  DirDeletedEvent,\
  DirCreatedEvent,\
  DirModifiedEvent,\
  FileMovedEvent,\
  FileDeletedEvent,\
  FileCreatedEvent,\
  FileModifiedEvent


# NOTE(termie): A significant portion of the code below is to work around
#               editors that, in their default behavior, don't trigger
#               file modification system events.
#               Instead of listening for the events we poll mtime and
#               trigger even if the inode has changed.


# NOTE(termie): this is mostly a copy-paste a small edit to ignore the
#               inode when checking the mtime of a path.
class SimplerDiff(dirsnapshot.DirectorySnapshotDiff):
  def __init__(self, ref_dirsnap, dirsnap):
    """
    """
    self._files_deleted = list()
    self._files_modified = list()
    self._files_created = list()
    self._files_moved = list()

    self._dirs_modified = list()
    self._dirs_moved = list()
    self._dirs_deleted = list()
    self._dirs_created = list()

    paths_moved_from_not_deleted = []
    paths_deleted = set()
    paths_created = set()

    # Detect modifications and distinguish modifications that are actually
    # renames of files on top of existing file names (OS X/Linux only)
    for path, stat_info in list(dirsnap.stat_snapshot.items()):
      if path in ref_dirsnap.stat_snapshot:
        ref_stat_info = ref_dirsnap.stat_info(path)
        if stat_info.st_mtime != ref_stat_info.st_mtime:
          if stat.S_ISDIR(stat_info.st_mode):
            self._dirs_modified.append(path)
          else:
            self._files_modified.append(path)
        elif stat_info.st_ino != ref_stat_info.st_ino:
          # Same path exists... but different inode
          if ref_dirsnap.has_inode(stat_info.st_ino):
            old_path = ref_dirsnap.path_for_inode(stat_info.st_ino)
            paths_moved_from_not_deleted.append(old_path)
            if stat.S_ISDIR(stat_info.st_mode):
              self._dirs_moved.append((old_path, path))
            else:
              self._files_moved.append((old_path, path))
          else:
            # we have a newly created item with existing name,
            # but different inode
            paths_deleted.add(path)
            paths_created.add(path)

    paths_deleted = paths_deleted | ((ref_dirsnap.paths - dirsnap.paths)
                                     - set(paths_moved_from_not_deleted))
    paths_created = paths_created | (dirsnap.paths - ref_dirsnap.paths)

    # Detect all the moves/renames except for atomic renames on top of
    # existing files that are handled in the file modification check
    # for-loop above
    # Doesn't work on Windows since st_ino is always 0, so exclude on Windows.
    if not sys.platform.startswith('win'):
      for created_path in paths_created:
        created_stat_info = dirsnap.stat_info(created_path)
        for deleted_path in paths_deleted:
          deleted_stat_info = ref_dirsnap.stat_info(deleted_path)
          if created_stat_info.st_ino == deleted_stat_info.st_ino:
            paths_deleted.remove(deleted_path)
            paths_created.remove(created_path)
            if stat.S_ISDIR(created_stat_info.st_mode):
              self._dirs_moved.append((deleted_path, created_path))
            else:
              self._files_moved.append((deleted_path, created_path))

    # Now that we have renames out of the way, enlist the deleted and
    # created files/directories.
    for path in paths_deleted:
      stat_info = ref_dirsnap.stat_info(path)
      if stat.S_ISDIR(stat_info.st_mode):
        self._dirs_deleted.append(path)
      else:
        self._files_deleted.append(path)

    for path in paths_created:
      stat_info = dirsnap.stat_info(path)
      if stat.S_ISDIR(stat_info.st_mode):
        self._dirs_created.append(path)
      else:
        self._files_created.append(path)


# NOTE(termie): this is mostly a copy-paste with a small edit to use
#               SimplerDiff
class SimplerPollingEmitter(polling.PollingEmitter):
  def queue_events(self, timeout):
    # We don't want to hit the disk continuously.
    # timeout behaves like an interval for polling emitters.
    time.sleep(timeout)

    with self._lock:

      if not self._snapshot:
        return

      # Get event diff between fresh snapshot and previous snapshot.
      # Update snapshot.
      new_snapshot = dirsnapshot.DirectorySnapshot(
          self.watch.path, self.watch.is_recursive)
      events = SimplerDiff(self._snapshot, new_snapshot)
      self._snapshot = new_snapshot

      # Files.
      for src_path in events.files_deleted:
        self.queue_event(FileDeletedEvent(src_path))
      for src_path in events.files_modified:
        self.queue_event(FileModifiedEvent(src_path))
      for src_path in events.files_created:
        self.queue_event(FileCreatedEvent(src_path))
      for src_path, dest_path in events.files_moved:
        self.queue_event(FileMovedEvent(src_path, dest_path))

      # Directories.
      for src_path in events.dirs_deleted:
        self.queue_event(DirDeletedEvent(src_path))
      for src_path in events.dirs_modified:
        self.queue_event(DirModifiedEvent(src_path))
      for src_path in events.dirs_created:
        self.queue_event(DirCreatedEvent(src_path))
      for src_path, dest_path in events.dirs_moved:
        self.queue_event(DirMovedEvent(src_path, dest_path))


class SimplerPollingObserver(api.BaseObserver):
  """
  Observer thread that schedules watching directories and dispatches
  calls to event handlers.
  """

  def __init__(self, timeout=api.DEFAULT_OBSERVER_TIMEOUT):
    api.BaseObserver.__init__(
        self, emitter_class=SimplerPollingEmitter, timeout=timeout)


class CommandEventHandler(events.FileSystemEventHandler):
  exclude = ['.*\.pyc', '\..*\.swp']

  def __init__(self, command, *args, **kw):
    super(CommandEventHandler, self).__init__(*args, **kw)
    self.command = command
    self._executing = threading.Semaphore(1)
    self._should_execute = threading.Event()

    o = []
    for matcher in self.exclude:
      if type(matcher) is type(''):
        o.append(re.compile(matcher))
      else:
        o.append(matcher)

    self.exclude = o

  def dispatch(self, event):
    for matcher in self.exclude:
      if matcher.match(os.path.basename(event.src_path)):
        return
    # Ignore dirmodifieds
    if isinstance(event, events.DirModifiedEvent):
      return
    super(CommandEventHandler, self).dispatch(event)

  def on_any_event(self, event):
    self.execute_command()

  def execute_command(self):
    self._should_execute.set()
    self._executing.acquire()
    if not self._should_execute.is_set():
      self._executing.release()
      return

    # Alright, we're the winners
    self._should_execute.clear()
    try:
      subprocess.call(self.command, stdout=sys.stdout, shell=True)
    finally:
      self._executing.release()


def get_parser():
  parser = argparse.ArgumentParser(
      description='Watch a path and trigger contrail actions')
  parser.add_argument('-p', '--path', help='path to watch')
  parser.add_argument('command')
  return parser


def main():
  parser = get_parser()
  args = parser.parse_args()

  path = args.path or '.'

  event_handler = CommandEventHandler(args.command)
  observer = SimplerPollingObserver()
  observer.schedule(event_handler, path=path, recursive=True)
  observer.start()
  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    observer.stop()

  observer.join()


if __name__ == '__main__':
  main()
