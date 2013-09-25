import os
import sys

from fabric import main as fab




def main():
    """Load our default fabfile, then attempt to load any local fabfiles."""
    our_fab = os.path.join(os.path.dirname(__file__), 'default_fabfile.py')
    docstring, callables, default = fab.load_fabfile(our_fab)
    fab.state.commands.update(callables)


    fabfiles = []
    other_fab = fab.find_fabfile()
    if other_fab:
      fabfiles.append(other_fab)

    fabfiles.append(our_fab)


    fab.main(fabfiles)
