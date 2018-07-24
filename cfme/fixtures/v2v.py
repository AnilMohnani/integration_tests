import pytest

from widgetastic.utils import partial_match

from cfme.fixtures.provider import setup_or_skip
from cfme.utils.generators import random_vm_name


@pytest.fixture(scope="function")
def migration_ui(appliance):
    """Fixture to enable migration UI"""
    appliance.enable_migration_ui()
    yield
    appliance.disable_migration_ui()


@pytest.fixture(scope='function')
def provider_setup(migration_ui, request, second_provider, provider):
    """Fixture to setup nvc and rhv provider"""
    setup_or_skip(request, second_provider)
    setup_or_skip(request, provider)
    yield second_provider, provider
    second_provider.delete_if_exists(cancel=False)
    provider.delete_if_exists(cancel=False)


@pytest.fixture(scope='function')
def host_creds(provider_setup):
    """Add credentials to conversation host"""
    provider = provider_setup[0]
    host = provider.hosts.all()[0]
    host_data, = [data for data in provider.data['hosts'] if data['name'] == host.name]
    host.update_credentials_rest(credentials=host_data['credentials'])
    yield host
    host.remove_credentials_rest()


@pytest.fixture(scope='function')
def conversion_tags(appliance, host_creds):
    """Assigning tags to conversation host"""
    tag1 = appliance.collections.categories.instantiate(
        display_name='V2V - Transformation Host *').collections.tags.instantiate(
        display_name='t')
    tag2 = appliance.collections.categories.instantiate(
        display_name='V2V - Transformation Method').collections.tags.instantiate(
        display_name='VDDK')
    host_creds.add_tags(tags=(tag1, tag2))
    yield
    host_creds.remove_tags(tags=(tag1, tag2))


def get_vm(request, appliance, nvc_prov, template, datastore):
    """Fixture to provide vm object"""
    source_datastores_list = nvc_prov.data.get('datastores')
    source_datastore = [d.name for d in source_datastores_list if d.type == datastore][0]
    collection = nvc_prov.appliance.provider_based_collection(nvc_prov)
    vm_obj = collection.instantiate(random_vm_name('v2v'),
                                    nvc_prov,
                                    template_name=template(nvc_prov)['name'])

    request.addfinalizer(lambda: vm_obj.cleanup_on_provider())
    vm_obj.create_on_provider(timeout=2400, find_in_cfme=True, allow_skip="default",
         datastore=source_datastore)
    return vm_obj


def _form_data_cluster_mapping(nvc_prov, rhvm_prov):
    # since we have only one cluster on providers
    source_cluster = second_provider.data.get('clusters')[0]
    target_cluster = provider.data.get('clusters')[0]

    if not source_cluster or not target_cluster:
        pytest.skip("No data for source or target cluster in providers.")

    return {
        'sources': [partial_match(source_cluster)],
        'target': [partial_match(target_cluster)]
    }


def _form_data_datastore_mapping(second_provider, provider, source_type, target_type):
    source_datastores_list = second_provider.data.get('datastores')
    target_datastores_list = provider.data.get('datastores')

    if not source_datastores_list or not target_datastores_list:
        pytest.skip("No data for source or target cluster in providers.")

    # assuming, we just have 1 datastore of each type
    source_datastore = [d.name for d in source_datastores_list if d.type == source_type][0]
    target_datastore = [d.name for d in target_datastores_list if d.type == target_type][0]

    return {
        'sources': [partial_match(source_datastore)],
        'target': [partial_match(target_datastore)]
    }


def _form_data_network_mapping(second_provider, provider, source_network_name, target_network_name):
    source_vlans_list = second_provider.data.get('vlans')
    target_vlans_list = provider.data.get('vlans')

    if not source_vlans_list or not target_vlans_list:
        pytest.skip("No data for source or target cluster in providers.")

    # assuming there will be only 1 network matching given name
    source_network = [v for v in source_vlans_list if v == source_network_name][0]
    target_network = [v for v in target_vlans_list if v == target_network_name][0]

    return {
        'sources': [partial_match(source_network)],
        'target': [partial_match(target_network)]
    }


@pytest.fixture(scope='function')
def form_data_vm_obj_single_datastore(request, appliance, nvc_prov, rhvm_prov):
    """Return Infra Mapping form data and vm_obj, encapsulated in list,
       deployed on correct Datastore for migration."""
    form_data = (
        {
            'general': {
                'name': 'infra_map_{}'.format(fauxfactory.gen_alphanumeric()),
                'description': "Single Datastore migration of VM from {ds_type1} to"
                " {ds_type2},".format(ds_type1=request.param[0], ds_type2=request.param[1])
            },
            'cluster': {
                'mappings': [_form_data_cluster_mapping(second_provider, provider)]
            },
            'datastore': {
                'Cluster ({})'.format(provider.data.get('clusters')[0]): {
                    'mappings': [_form_data_datastore_mapping(second_provider, provider,
                        request.param[0], request.param[1])]
                }
            },
            'network': {
                'Cluster ({})'.format(provider.data.get('clusters')[0]): {
                    'mappings': [_form_data_network_mapping(second_provider, provider,
                        'VM Network', 'ovirtmgmt')]
                }
            }
        })
    vm_obj = get_vm(request, appliance, nvc_prov, request.param[2], request.param[0])
    return form_data, [vm_obj]


@pytest.fixture(scope='function')
def form_data_single_network(request, second_provider, provider):
    form_data = (
        {
            'general': {
                'name': 'infra_map_{}'.format(fauxfactory.gen_alphanumeric()),
                'description': "Single Network migration of VM from {vlan1} to {vlan2},".
                format(vlan1=request.param[0], vlan2=request.param[1])
            },
            'cluster': {
                'mappings': [_form_data_cluster_mapping(second_provider, provider)]
            },
            'datastore': {
                'Cluster ({})'.format(provider.data.get('clusters')[0]): {
                    'mappings': [_form_data_datastore_mapping(second_provider, provider,
                        'nfs', 'nfs')]
                }
            },
            'network': {
                'Cluster ({})'.format(provider.data.get('clusters')[0]): {
                    'mappings': [_form_data_network_mapping(second_provider, provider,
                        request.param[0], request.param[1])]
                }
            }
        })
    return form_data


@pytest.fixture(scope='function')
def form_data_dual_datastore(request, second_provider, provider):
    vmware_nw = second_provider.data.get('vlans')[0]
    rhvm_nw = provider.data.get('vlans')[0]

    if not vmware_nw or not rhvm_nw:
        pytest.skip("No data for source or target network in providers.")

    form_data = (
        {
            'general': {
                'name': 'infra_map_{}'.format(fauxfactory.gen_alphanumeric()),
                'description': "Dual Datastore migration of VM from {} to {},"
                "& from {} to {}".
                format(request.param[0][0], request.param[0][1], request.param[1][0],
                    request.param[1][1])
            },
            'cluster': {
                'mappings': [_form_data_cluster_mapping(second_provider, provider)]
            },
            'datastore': {
                'Cluster ({})'.format(provider.data.get('clusters')[0]): {
                    'mappings': [_form_data_datastore_mapping(second_provider, provider,
                            request.param[0][0], request.param[0][1]),
                        _form_data_datastore_mapping(second_provider, provider,
                            request.param[1][0], request.param[1][1])
                    ]
                }
            },
            'network': {
                'Cluster ({})'.format(provider.data.get('clusters')[0]): {
                    'mappings': [_form_data_network_mapping(second_provider, provider,
                        second_provider.data.get('vlans')[0], provider.data.get('vlans')[0])]
                }
            }
        })
    return form_data


@pytest.fixture(scope="module")
def enable_disable_migration_ui(appliance):
    appliance.enable_migration_ui()
    yield
    appliance.disable_migration_ui()
