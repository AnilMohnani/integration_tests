# -*- coding: utf-8 -*-
"""Test Service Details page functionality."""
import pytest

from cfme import test_requirements
from cfme.cloud.provider import CloudProvider
from cfme.cloud.provider.azure import AzureProvider
from cfme.cloud.provider.ec2 import EC2Provider
from cfme.infrastructure.provider import InfraProvider
from cfme.markers.env_markers.provider import ONE_PER_TYPE
from cfme.markers.env_markers.provider import providers
from cfme.services.myservice import MyService
from cfme.services.myservice.ssui import DetailsMyServiceView
from cfme.utils.appliance import ViaSSUI
from cfme.utils.providers import ProviderFilter
from cfme.utils.wait import wait_for

pytestmark = [
    pytest.mark.meta(server_roles="+automate"),
    test_requirements.ssui,
    pytest.mark.long_running,
    pytest.mark.provider(
        selector=ONE_PER_TYPE,
        gen_func=providers,
        filters=[ProviderFilter(
            classes=[InfraProvider, CloudProvider],
            required_fields=['provisioning'])])
]


@pytest.mark.rhv1
@pytest.mark.parametrize('context', [ViaSSUI])
def test_myservice_crud(appliance, setup_provider, context, order_service):
    """Test Myservice crud in SSUI.

    Metadata:
        test_flag: ssui, services

    Polarion:
        assignee: nansari
        casecomponent: SelfServiceUI
        initialEstimate: 1/4h
        tags: ssui
    """
    catalog_item = order_service
    with appliance.context.use(context):
        my_service = MyService(appliance, catalog_item.name)
        my_service.set_ownership("Administrator", "EvmGroup-approver")
        my_service.update({'description': '{}_edited'.format(catalog_item.name)})
        my_service.edit_tags("Cost Center", "Cost Center 002")
        my_service.delete()


@pytest.mark.parametrize('context', [ViaSSUI])
def test_retire_service_ssui(appliance, setup_provider,
                        context, order_service, request):
    """Test retire service.

    Metadata:
        test_flag: ssui, services

    Polarion:
        assignee: nansari
        casecomponent: SelfServiceUI
        initialEstimate: 1/4h
        tags: ssui
    """
    catalog_item = order_service
    with appliance.context.use(context):
        my_service = MyService(appliance, catalog_item.name)
        my_service.retire()

        @request.addfinalizer
        def _finalize():
            my_service.delete()


@pytest.mark.rhv3
@pytest.mark.parametrize('context', [ViaSSUI])
def test_service_start(appliance, setup_provider, context,
                       order_service, provider, request):
    """Test service stop

    Metadata:
        test_flag: ssui, services

    Polarion:
        assignee: nansari
        casecomponent: SelfServiceUI
        initialEstimate: 1/4h
        tags: ssui
    """
    catalog_item = order_service
    with appliance.context.use(context):
        my_service = MyService(appliance, catalog_item.name)
        if provider.one_of(InfraProvider, EC2Provider, AzureProvider):
            # For Infra providers vm is provisioned.Hence Stop option is shown
            # For Azure, EC2 Providers Instance is provisioned.Hence Stop option is shown
            my_service.service_power(power='Stop')
            view = my_service.create_view(DetailsMyServiceView)
            wait_for(lambda: view.resource_power_status.power_status == 'Off',
                     timeout=1000,
                     fail_condition=None,
                     message='Wait for resources off',
                     delay=20)
        else:
            my_service.service_power(power='Start')
            view = my_service.create_view(DetailsMyServiceView)
            wait_for(lambda: view.resource_power_status.power_status == 'On',
                     timeout=1000,
                     fail_condition=None,
                     message='Wait for resources on',
                     delay=20)

        @request.addfinalizer
        def _finalize():
            my_service.delete()


@pytest.mark.manual
@test_requirements.ssui
@pytest.mark.tier(2)
@pytest.mark.parametrize('context', [ViaSSUI])
def test_suspend_vm_service_details(context):
    """
    Test suspending VM from SSUI service details page.

    Polarion:
        assignee: apagac
        casecomponent: Infra
        caseimportance: medium
        initialEstimate: 1/4h
        setup:
            1. Have a service catalog item that provisions a VM
        testSteps:
            1. In SSUI, navigate to My Services -> <service name> to see service details
            2. In Resources section, choose 'Suspend' from dropdown
        expectedResults:
            1. Service details displayed
            2. VM is suspended; VM is NOT in Unknown Power State
    Bugzilla:
        1670373
    """
    pass


@pytest.mark.meta(coverage=[1677744])
@pytest.mark.manual
@pytest.mark.ignore_stream('5.10')
@pytest.mark.tier(2)
def test_no_error_while_fetching_the_service():
    """

    Bugzilla:
        1677744

    Polarion:
        assignee: nansari
        startsin: 5.11
        casecomponent: SelfServiceUI
        initialEstimate: 1/6h
        testSteps:
            1. Provision service in regular UI with user that isn't admin
            2. Delete user, then go view the service in the SUI and see if it blows up.
        expectedResults:
            1.
            2. In SUI click on provisioned service
    """
    pass


@pytest.mark.meta(coverage=[1628520])
@pytest.mark.manual
@pytest.mark.ignore_stream('5.10')
@pytest.mark.tier(2)
def test_retire_owned_service():
    """

    Bugzilla:
        1628520

    Polarion:
        assignee: nansari
        startsin: 5.11
        casecomponent: SelfServiceUI
        initialEstimate: 1/6h
        testSteps:
            1. Create a catalog item as User
            2. Provision service in regular UI with user
            3. Login to Service UI as User
            4. Try to retire the service
        expectedResults:
            1.
            2.
            3.
            4. Service should retire
    """
    pass


@pytest.mark.meta(coverage=[1695804])
@pytest.mark.manual
@pytest.mark.ignore_stream('5.10')
@pytest.mark.tier(2)
def test_service_dialog_check_on_ssui():
    """
    Bugzilla:
        1695804
    Polarion:
        assignee: nansari
        startsin: 5.11
        casecomponent: SelfServiceUI
        initialEstimate: 1/6h
        testSteps:
            1. Import datastore and import dialog
            2. Add catalog item with above dialog
            3. Navigate to order page of service
            4. Order the service
            5. Login into SSUI Portal
            6. Go MyService and click on provisioned service
        expectedResults:
            1.
            2.
            3.
            4.
            5.
            6. Automation code shouldn't load when opening a service
    """
    pass


@pytest.mark.meta(coverage=[1743734])
@pytest.mark.manual
@pytest.mark.ignore_stream('5.10')
@pytest.mark.tier(2)
def test_list_supported_languages_on_ssui():
    """
    Bugzilla:
        1743734

    Polarion:
        assignee: nansari
        startsin: 5.11
        caseimportance: medium
        casecomponent: SelfServiceUI
        initialEstimate: 1/16h
        testSteps:
            1. Log into SSUI, see what languages are available
        expectedResults:
            1. Service UI should list the Supported languages:
    """
    pass
