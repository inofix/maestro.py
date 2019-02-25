# Directory in which we're working'
WORKDIR='./workdir'

# the merge of the above inventories will be stored here
INVENTORYDIR = './.inventory'

# some "sane" ansible default values
ANSIBLE_MANAGED='Ansible managed. All local changes will be lost!'
ANSIBLE_TIMEOUT='60'
ANSIBLE_SCP_IF_SSH='True'
ANSIBLE_GALAXY_ROLES='.ansible-galaxy-roles'
ANSIBLE_CONNECT = '/usr/share/reclass/reclass-ansible'

# file name of the galaxy role definition (relative to the playbookdirs)
GALAXYROLES="galaxy/roles.yml"

RECLASS_CONFIG_INITIAL = '''
storage_type: yaml_fs
inventory_base_uri: {}
'''.format(INVENTORYDIR)

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
    inventorydir=INVENTORYDIR,
    ansible_timeout=ANSIBLE_TIMEOUT,
    ansible_managed=ANSIBLE_MANAGED,
    maestrodir='.',
    ansible_galaxy_roles=ANSIBLE_GALAXY_ROLES,
    ansible_scp_if_ssh=ANSIBLE_SCP_IF_SSH
)
