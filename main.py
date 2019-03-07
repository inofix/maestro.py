import imp
import os
import pathlib
import re
import shutil
import subprocess
import sys

from git.repo.base import Repo
import click
import yaml

from maestro import settings


# source the local python config file
with open('.maestro.py') as f:
    settings.__dict__.update(imp.load_module(
        'conf',
        f,
        '.maestro.py',
        ('.py', 'rb', imp.PY_SOURCE)
    ).__dict__)


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

@main.command()
def list():
    nodes = get_nodes()
    process_nodes(list_node, nodes)

@main.command()
def reclass():
    print_plain_reclass()

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
            print('clone repository {}'.format(git_dest))
            os.makedirs(git_dest, exist_ok=True)
            Repo.clone_from(repository_remote, git_dest)

def do_reinit():
    print('Re-create the inventory. Note: there will be warnings for duplicates, etc.')
    to_reinit = ['nodes', 'classes']

    for _dir in to_reinit:
        to_refresh = '{}/{}'.format(settings.INVENTORYDIR, _dir)
        shutil.rmtree(to_refresh, ignore_errors=True)
        os.makedirs(to_refresh)

    for idir in settings.inventorydirs.values():
        for _dir in to_reinit:
            copy_directories_and_yaml(idir, _dir)

    print('Re-connect ansible to our reclass inventory')

    if os.path.isfile('{}/hosts'.format(settings.INVENTORYDIR)):
        os.remove('{}/hosts'.format(settings.INVENTORYDIR))
    if os.path.isfile('{}/reclass-config.yml'.format(settings.INVENTORYDIR)):
        os.remove('{}/reclass-config.yml'.format(settings.INVENTORYDIR))

    if not os.path.isfile(settings.ANSIBLE_CONNECT):
        error('reclass is not installed (looked in {})'.format(settings.ANSIBLE_CONNECT))
    os.symlink(settings.ANSIBLE_CONNECT, '{}/hosts'.format(settings.INVENTORYDIR))

    # TODO: checkout $_pre
    if True:
        with open('{}/reclass-config.yml'.format(settings.INVENTORYDIR), 'w+') as f:
            f.write(settings.RECLASS_CONFIG_INITIAL)
            print('Installed reclass config')

        with open('./ansible.cfg', 'w+') as f:
            f.write(settings.ANSIBLE_CONFIG_INITIAL)
            print('Installed ansible config')
    # TODO: check how/why to assign $ANSIBLE_CONFIG

    print('Installing all necessary ansible-galaxy roles')
    for _dir in settings.playbookdirs.values():
        f = '{}/{}'.format(_dir, settings.GALAXYROLES)
        if not os.path.isfile(f):
            continue
        print('Found {}'.format(f))
        
        with open(f) as fi:
            lines = fi.readlines()
        if not any(re.match(r'^- src:', line) for line in lines):
            print(' .. but it was empty, ignoring..')
            continue
            
        if subprocess.call([settings.ANSIBLE_GALAXY, 'install', '-r', f]):
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

def copy_directories_and_yaml(frm, subdir):
    frm = os.path.abspath(frm)
    for (dirpath, _, filenames) in os.walk('{}/{}'.format(frm, subdir)):
        os.makedirs(dirpath.replace(frm, settings.INVENTORYDIR), exist_ok=True)
        for fname in filenames:
            if fname.endswith('.yml'):
                path = '{}/{}'.format(dirpath, fname)
                os.symlink(path, path.replace(frm, settings.INVENTORYDIR))

# First call to reclass to get an overview of the hosts available
def get_nodes():
    nodes_path = '{}/nodes'.format(settings.INVENTORYDIR)
    if not os.path.isdir(nodes_path):
        error('reclass environment not found at {}'.format(nodes_path))

    reclass_filter = ''
    if len(settings.PROJECTFILTER):
        if os.path.isdir('{}/{}'.format(nodes_path, settings.PROJECTFILTER)):
            reclass_filter = '-u nodes/{}'.format(settings.PROJECTFILTER)
        else:
            error('This project does not exist in {}'.format(settings.INVENTORYDIR))
    reclass_result = subprocess.run(['reclass', '-b', settings.INVENTORYDIR, '-i'], capture_output=True)
    yamlresult = yaml.load(reclass_result.stdout)

    # TODO: process_nodes process_classes etc.
    return yamlresult['nodes']

def list_node(name, properties):
    project = properties['__reclass__']['node'].split('/')[0]
    output = '{} ({}:{}) {} ({}-{} {})'.format(name, properties.get('environment'), project, properties['parameters'].get('role'), properties['parameters'].get('os__distro'), properties['parameters'].get('os__codename'), properties['parameters'].get('os__release'))
    print(output)

def process_nodes(command, nodes):
    for key, value in sorted(nodes.items(), reverse=True):
        command(key, value)



def print_plain_reclass():
    print('plain reclass')
    dirStructure = os.walk('{}/nodes/'.format(settings.INVENTORYDIR))
    filterednodes = []
    # TODO: remove True, and add CLI setting for filters
    if True or len(settings.NODEFILTER):
        for (dirpath, dirnames, filenames) in dirStructure:
            print(dirpath, dirnames, filenames)
        # TODO: assign nodefilter variable with reclass
        pass
    else:
        reclassmode = '-i'
    
    if len(settings.NODEFILTER):
        nodes_uri = '{}/nodes/'.format()

    if len(settings.PROJECTFILTER):
        nodes_uri = '{}/nodes/{}'.format(settings.INVENTORYDIR, settings.PROJECTFILTER)
        if not os.path.isdir(nodes_uri):
            error('No such project dir: {}'.format(nodes_uri))
    elif len(settings.CLASSFILTER):
        error("Classes are not supported here, use project filter instead") 

    if len(nodes_uris):
        reclass_result = subprocess.run(
            ['reclass', '-b', '-u', modes_uri, reclassmode],
            capture_output=True
        )
        print('reclass_result', reclass_result)
    else:
        reclass_result = subprocess.run(
            ['reclass', '-b', modes_uri, reclassmode],
            capture_output=True
        )
        print('reclass_result', reclass_result)

# def print_warning(param):
#     if verbose > 1:
#         click.secho('Warning', fg='yellow')
#         print('Warning')
