import os
import pathlib
import re
import shutil
import subprocess
import sys

import click
from git.repo.base import Repo

from maestro import settings
import imp

# source the local python config file
with open('.maestro.py') as f:
    settings.__dict__.update(imp.load_module(
        'conf',
        f,
        '.maestro.py',
        ('.py', 'rb', imp.PY_SOURCE)
    ).__dict__)

#
# variables
#

# the merge of the above inventories will be stored here
inventorydir = './.inventory'

# some "sane" ansible default values
ansible_managed='Ansible managed. All local changes will be lost!'
ansible_timeout='60'
ansible_scp_if_ssh='True'
ansible_galaxy_roles='.ansible-galaxy-roles'

# file name of the galaxy role definition (relative to the playbookdirs)
galaxyroles="galaxy/roles.yml"

RECLASS_CONFIG_INITIAL = '''
storage_type: yaml_fs
inventory_base_uri: {}
'''.format(inventorydir)

ANSIBLE_CONFIG_INITIAL = '''
[defaults]
hostfile    = {inventorydir}/hosts
timeout     = {ansible_timeout}
ansible_managed = "{ansible_managed}"
roles_path  = {maestrodir}/{ansible_galaxy_roles}
#allow_world_readable_tmpfiles = true

[ssh_connection]
#scp_if_ssh = {ansible_scp_if_ssh}
'''.format(
    inventorydir=inventorydir,
    ansible_timeout=ansible_timeout,
    ansible_managed=ansible_managed,
    maestrodir='.',
    ansible_galaxy_roles=ansible_galaxy_roles,
    ansible_scp_if_ssh=ansible_scp_if_ssh
)

#
# CLI commands
#

@click.group()
def main():
    pass

@main.command()
def init():
    initialize_workdir()
    do_init()
    do_reinit()

@main.command()
def reinit():
    initialize_workdir()
    do_reinit()

#
# Functions
#
def print_usage():
    print('usage: {} [option] action'.format(sys.argv[0]))

def error(*args):
    print_usage()
    print('Error: {}'.format(''.join(str(x) for x in args)))
    sys.exit(1)

def do_init():
    for repository_name, repository_remote in settings.toclone.items():
        git_dest = ''
        if repository_name in settings.inventorydirs:
            git_dest = settings.inventorydirs[repository_name]
        elif repository_name in settings.playbookdirs:
            git_dest = settings.playbookdirs[repository_name]
        elif repository_name in settings.localdirs:
            git_dest = settings.localdirs[repository_name]
        else:
            print('there is no corresponding directory defined in your config for {}'.format(repository))

        if not git_dest:
            print('could not find git_dest')
            continue

        if os.path.isdir('{}/.git'.format(git_dest)):
            print('update repository {}'.format(git_dest))
            git = Repo(git_dest).git
            git.pull()
        else:
            os.makedirs(git_dest, exist_ok=True)
            Repo.clone_from(repository_remote, git_dest)
    do_reinit()

def copy_directories_and_yaml(frm, subdir):
    for (f, _, filenames) in os.walk('{}/{}'.format(frm, subdir)):
        os.makedirs(f.replace(frm, inventorydir), exist_ok=True)
        for fname in filenames:
            if fname.endswith('.yml'):
                path = '{}/{}'.format(f, fname)
                os.symlink(path, path.replace(frm, inventorydir))

def do_reinit():
    print('Re-create the inventory. Note: there will be warnings for')
    print('duplicates, etc.')
    to_reinit = ['nodes', 'classes']

    for _dir in to_reinit:
        to_refresh = '{}/{}'.format(inventorydir, _dir)
        shutil.rmtree(to_refresh, ignore_errors=True)
        os.makedirs(to_refresh)

    for idir in settings.inventorydirs.values():
        for _dir in to_reinit:
            copy_directories_and_yaml(idir, _dir)

    print('Re-connect ansible to our reclass inventory')

    if os.path.isfile('{}/hosts'.format(inventorydir)):
        os.remove('{}/hosts'.format(inventorydir))
    if os.path.isfile('{}/reclass-config.yml'.format(inventorydir)):
        os.remove('{}/reclass-config.yml'.format(inventorydir))

    if not os.path.isfile(settings.ansible_connect):
        error('reclass is not installed (looked in {})'.format(settings.ansible_connect))
    os.symlink(settings.ansible_connect, '{}/hosts'.format(inventorydir))
    # TODO: checkout $_pre
    if True:
        with open('{}/reclass-config.yml'.format(inventorydir), 'w+') as f:
            f.write(RECLASS_CONFIG_INITIAL)

        with open('{}/ansible.cfg'.format(inventorydir), 'w+') as f:
            f.write(ANSIBLE_CONFIG_INITIAL)
    # TODO: check how/why to assign $ANSIBLE_CONFIG

    print('Installing all necessary ansible-galaxy roles')
    for _dir in settings.playbookdirs.values():
        f = '{}/{}'.format(_dir, galaxyroles)
        if not os.path.isfile(f):
            continue
        print('Found {}'.format(f))
        
        with open(f) as fi:
            lines = fi.readlines()
        if not any(re.match(r'^- src:', line) for line in lines):
            print(' .. but it was empty, ignoring..')
            continue
            
        if subprocess.call([settings.ansible_galaxy, 'install', '-r', f]):
            error(
                "ansible-galaxy failed to perform the" \
                "installation. Please make sure all the" \
                "roles do exist and that you have" \
                "write access to the ansible 'roles_path'," \
                "it can be controled in ansible.cfg in" \
                "the [defaults] section."
            )                    
        print('done')

def initialize_workdir():
    pathlib.Path(settings.WORKDIR).mkdir(parents=True, exist_ok=True)
