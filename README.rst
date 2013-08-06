Contrail: Iterate Faster
========================

Contrail is a tool for rapid deployment of development environments for
cloud-style applications.

It's goal is to provide a plethora of tools for teams and developers to speed
up common tasks and build the foundations for good practices.

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

Contrail will happily set up a Gitlab and Jenkins server, with associated
plugins [TODO], or if you're using Github associated config for that
instead [TODO].

To speed things up when iterating often (which you are going to do), an Apt
cache can be set up on a team or individual level.

Additionally, to help test against "real" data, a central staging database
can be set up [TODO] and refreshed [TODO].


Individual Tooling
------------------

The main annoyance in developing in a cloud-style environment is the number
of separate servers and services that all need to be managed in unison to
test changes.

Contrail suggests starting with a pretty standard-looking setup of having an
HAProxy server that backends to a multiple Nginx servers that in turn backend
to your app servers that backend to a single database [TODO]. This forces you to
consider (and allows you to check) the implications of multiple app servers,
concurrency and caching.

Additionally, for rapid development, Contrail knows how to configure your app
servers to run your app, and how to push new copies of your app to those
servers to test your new code. At the moment that involves Gunicorn with a WSGI
app [TODO] or Django, or Tomcat with tomcat apps [TODO].


Usage
-----

Build a skeleton config for a development environment, in this case
using Vagrant::

  contrail startdev --vagrant

At this point we should have a ``Vagrantfile`` and a ``fabfile.py`` in our
current directory.



[TODO]


Configuration
-------------

[TODO]
