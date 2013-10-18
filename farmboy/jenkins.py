# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Original code based on https://github.com/ailling/jenkins-ubuntu-deployment/
# and https://github.com/termie/jenkins-ubuntu-deployment/

import fabtools.require

from fabric.api import env
from fabric.api import execute
from fabric.api import local
from fabric.api import sudo
from fabric.api import roles
from fabric.api import run
from fabric.api import task


@roles('ci')
@task
def jenkins_repo():
    fabtools.require.files.file(
        url = 'http://pkg.jenkins-ci.org/debian/jenkins-ci.org.key',
        path = '/tmp/jenkins-ci.org.key')
    sudo('apt-key add /tmp/jenkins-ci.org.key')
    fabtools.require.files.file(
        contents='deb http://pkg.jenkins-ci.org/debian binary/',
        path='/etc/apt/sources.list.d/jenkins.list',
        use_sudo=True)


@roles('ci')
@task
def depends():
    fabtools.deb.update_index(quiet=False)


@roles('ci')
@task
def jenkins():
    fabtools.require.deb.packages([
        'jenkins',
    ])


@roles('ci')
@task
def nginx():
    fabtools.require.deb.packages([
        'nginx',
    ])
    fabtools.require.file(
        source   = 'files/nginx/jenkins',
        path     = '/etc/nginx/sites-available/jenkins',
        owner    = 'root',
        group    = 'root',
        mode     = '755',
        use_sudo = True)
    sudo('rm -f /etc/nginx/sites-enabled/jenkins')
    sudo('ln -s /etc/nginx/sites-available/jenkins'
         ' /etc/nginx/sites-enabled/jenkins')
    sudo('service nginx restart')


def setup_ssh_keys():
    sudo('ssh-keygen -t rsa', user='jenkins')
    run('echo "your deploy key:"')
    sudo('cat /var/lib/jenkins/.ssh/id_rsa.pub')


@roles('ci')
@task
def deploy():
    """Deploy a Jenkins server to the <ci> host."""
    #setup_machine()
    #setup_apache()
    #if auth_username:
    #    setup_basic_auth_user(auth_username)
    #upload_config(auth_username)
    #enable_apache_site()
    #setup_ssh_keys()
    execute(jenkins_repo)
    execute(depends)
    execute(jenkins)
    execute(nginx)


@roles('ci')
@task
def test_clone_repo(repourl=''):
    if not repourl:
        print 'Specify a repository url'
        return

    path = '/var/lib/jenkins/test_clone'
    sudo('rm -Rf %s' % path)
    sudo('mkdir %s' % path, user='jenkins')
    sudo('chown jenkins:nogroup %s' % path)
    sudo('cd %s; git clone %s' % (path, repourl), user='jenkins')
    sudo('rm -Rf %s' % path)


__all__ = ['deploy']
