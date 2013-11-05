FarmBoy: Let Us Do The Chores
==============================

FarmBoy is a tool and library for rapid deployment and development of
development environments for multi-system (cloud?) applications.

We take a developer-centric approach to managing your environments, ditching
the "Ops" in "DevOps" by providing a well-behaved library, instead of a
framework, and tools to take the leg-work out of working with that library.

We want the pieces of our library to work together in predictable ways so
that you can write your own additions and leverage our well-designed
internal architecture.

We hate opaque systems and try to be as transparent and easy to hack as
possible because *you are smart*.

And we want to make you even smarter by giving you the tools to try new
things quickly. We love test-driven development but sometimes making a
tiny code change and being able to manually test it right away will teach
you more about the problem, faster, than building the test framework to
replicate it.


Stuff We Know How To Configure Already
--------------------------------------

Supported backends are:

 * OpenStack using `novaclient` [TODO]
 * Vagrant
 * AWS using `boto`

Here are the supported tools so far:

 * Team:
  * Gitlab
  * Jenkins
  * Apt Cacher
  * Staging MySQL Database [TODO]
  * Staging PostgreSQL Database [TODO]
 * Individual
  * HAProxy
  * Nginx
  * Gunicorn
  * Django
  * PostgreSQL
  * MySQL [TODO]
  * Apt Cacher


Team Tooling
------------

At the core of any development team is version control, continuous integration,
and a shared staging environment.

FarmBoy will happily set up a Gitlab and Jenkins server, with associated
plugins [TODO], or if you're using Github associated config for that
instead [TODO].

To speed things up when iterating often (which you are going to do), an Apt
cache can be set up on a team or individual level.

Additionally, to help test against "real" data, a central staging database
can be set up [TODO] and refreshed [TODO].


Individual Tooling
------------------

A big annoyance in developing in a cloud-style environment is the number
of separate servers and services that all need to be managed in unison to
test changes.

FarmBoy suggests starting with a pretty standard-looking setup of having an
HAProxy server that backends to multiple Nginx servers that in turn backend
to your app servers that backend to a single database [TODO]. This forces you
to consider (and allows you to check) the implications of multiple app
servers, concurrency, caching and failover.

Additionally, for rapid development, FarmBoy knows how to configure your app
servers to run your app, and how to push new copies of your app to those
servers to test your new code. At the moment that involves Gunicorn with a WSGI
app [TODO] or Django, or Tomcat with tomcat apps [TODO].


Quickstart
----------

Build a skeleton config for a development environment, in this case
using Vagrant::

  farmboy vagrant.init

At this point we should have a ``Vagrantfile`` and a ``fabfile.py``, and
in our current directory. Take a look inside those to see what is going on,
they are well-documented.

Now, let's get you rollin::

  farmboy vagrant.build
  farmboy demo

That should do a whole bunch of work, and dump a url at the end for you
to admire your brand new Django site.


Command-line Usage
------------------

The `farmboy` command is basically a wrapper around `fab`. You can use
all the same options as one does with `fab`, we just add the various
FarmBoy taks by default. Using your own `fabfile.py` you can add to or
even override the defaults.

That said, there are some specific FarmBoy features that you are likely to
use when getting started::

  farmboy vagrant.init   # create an example vagrant environment in the
                         # current directory

  farmboy files.init     # [TODO] make a local copy of the various config file
                         # templates that farmboy uses so that you can
                         # override specific ones to work with your project

  farmboy openstack.init # [TODO] like vagrant.init but for OpenStack

  farmboy aws.init       # like vagrant.init but for AWS


For more commands try out `farmboy --list`.



Configuration
-------------

We've tried to be exceptionally verbose in the example fabfiles we provide
you with, so take a look in there after you do a farmboy <something>.init
or take a look at the template in files/farmboy/fabfile.py



Hosts / Roledefs / Network Config
--------------------------------

The cloud is a funny place. We're all pretty comfortable launching a virtual
machine at this point, but network configs are still a bit of a wild west.

Instead of trying to prescribe your network setups, FarmBoy gives you a
gracefully degrading set of tools to help you along your way for whatever
level of control over the network you may have.

------------
Full Control
------------

When you are using something like Vagrant for local VMs it is easy to assign
specific IPs that never have to change to your VMs. In these cases you can
accept the default configuration templates provided by FarmBoy.

See fabfile after `farmboy vagrant.init`.

The code is just templated, so should you want to make any changes, go ahead
and modify it to meet your requirements.


--------------
API Inspection
--------------

For plenty of public clouds running OpenStack or AWS compatible interfaces,
you'll likely want to launch the instances and then query the API for the
IPs you'll be using to interact with them.

For these situations, FarmBoy gives you a few templates for launching
instances in different environments that you can modify with your details,
and a tool to query your instances and cache the IP configuration locally.

See fabfile after `farmboy aws.init` and look at the code for
farmboy/aws.py:refresh.


--------------
Dynamic Lookup
--------------

You've got something crazy going on at your company and need to look up your
IPs from a custom database? You can define your hosts as a callable that will
be run every time you need to get the IPs for your setup. (We'd suggest caching
it locally, however, and using the caching wrapper FarmBoy provides [TODO])


---------
Hardcoded
---------

If you've got a specific setup, but no easy API access or one that is not
supported (yet?) by any of the predefined FarmBoy templates, you can simply
hardcode your IPs in the fabfile. FarmBoy understands that sometimes
hardcoding some config is simpler and faster than writing a dynamic lookup.



Design Goals
------------

FarmBoy is designed for developers and as such it aims to put the control
of everything in your hands. We try to use sensible defaults but we also
expect you to be a power user and want to tweak everything to fit the needs
of your particular project.


---------------------
1. Expose The Guts
---------------------

You're a smart person, we let you be smart.

In most cases FarmBoy is just a couple helpers for building fabfiles, the
definition documents that Fabric uses to run commands on remote servers. If
you already know Fabric (a well-known and powerful tool) you will have
a very easy time making modifications. If you don't already know it, plenty
of good documentation exists.

FarmBoy tries to explain and demonstrate the features of Fabric that it uses
in the fabfile it generates for you with hopes that you will be able to take
it from there.

The config file for FarmBoy is just the fabfile. And fabfiles are just
python. Go nuts.

After your initial setup you'll be using a regular fabfile to execute your
tasks. We just wrote a bunch of helpful tasks that interact well with each
other. If you want to write your own helpful tasks, just import them in the
fabfile.


----------
2. Be Real
----------

Stop making fake systems that look nothing like your production environment.

We want to codify best practices around these projects and make them easy
to use. In some cases this is a lofty goal, but at the very least we are
encouraging repeatability which is the first step to comparing usefulness
of an idea over time.

Sometimes being real is a pain, it would be much nicer to live in a world
where there were no race conditions and services never failed, but we don't.
Farm Boy should give you the tools to think in real terms and deal with real
problems.


--------------
3. Learn Stuff
--------------

Specifically stuff you don't want to try in production or would take
excessive effort to try in a staging environent.

Do you know how your app responds to failure? Kill off one of your app
hosts and see what happens in the proxy and cachers. Didn't work how you
expected? Reset things and try it again right away.

We don't have advanced tooling for it yet, but we'd love to integrate some
good libraries for simulating various kinds of network failures.
