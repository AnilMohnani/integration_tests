"""Test to validate basic navigations.Later to be replaced with End-to-End functional testing."""
import fauxfactory
import pytest
import time


from cfme.fixtures.provider import (rhel74_template, dual_network_template, dual_disk_template,
 dportgroup_template, win7_template, win10_template, win2016_template, rhel69_template,
 win2012_template, ubuntu16_template)
from cfme.infrastructure.provider.rhevm import RHEVMProvider
from cfme.infrastructure.provider.virtualcenter import VMwareProvider
from cfme.markers.env_markers.provider import ONE_PER_VERSION
from cfme.utils.appliance.implementations.ui import navigator
from cfme.utils.log import logger
from cfme.utils.wait import wait_for

pytestmark = [
    pytest.mark.ignore_stream('5.8'),
    pytest.mark.provider(
        classes=[RHEVMProvider],
        selector=ONE_PER_VERSION
    ),
    pytest.mark.provider(
        classes=[VMwareProvider],
        selector=ONE_PER_VERSION,
        fixture_name='second_provider'
    )
]


@pytest.mark.parametrize('form_data_vm_obj_single_datastore', [['nfs', 'nfs', rhel74_template],
                            ['nfs', 'iscsi', rhel74_template], ['iscsi', 'iscsi', rhel74_template],
                            ['iscsi', 'nfs', rhel74_template], ['iscsi', 'local', rhel74_template]],
                        indirect=True)
def test_single_datastore_single_vm_migration(request, appliance, provider_setup, host_creds,
                                            conversion_tags,
                                            form_data_vm_obj_single_datastore):
    infrastructure_mapping_collection = appliance.collections.v2v_mappings

    mapping = infrastructure_mapping_collection.create(form_data_vm_obj_single_datastore[0])
    request.addfinalizer(lambda: infrastructure_mapping_collection.delete(mapping))

    migration_plan_collection = appliance.collections.v2v_plans

    migration_plan = migration_plan_collection.create(
        name="plan_{}".format(fauxfactory.gen_alphanumeric()), description="desc_{}"
        .format(fauxfactory.gen_alphanumeric()), infra_map=mapping.name,
        vm_list=form_data_vm_obj_single_datastore[1], start_migration=True)

    # explicit wait for spinner of in-progress status card
    view = appliance.browser.create_view(navigator.get_class(migration_plan_collection, 'All').VIEW)
    wait_for(lambda: bool(view.progress_card.is_plan_started(migration_plan.name)),
        message="migration plan is starting, be patient please", delay=5, num_sec=150,
        handle_exception=True)

    def _get_plan_status():
        is_plan_visible = view.progress_card.is_plan_visible(migration_plan.name)
        if is_plan_visible:
            # log current status
            # uncomment following logs if github.com/ManageIQ/miq_v2v_ui_plugin/issues/415 fixed
            # logger.info("For plan %s, current migrated size is %s out of total size %s",
            #     migration_plan.name, view.progress_card.get_migrated_size(migration_plan.name),
            #     view.progress_card.get_total_size(migration_plan.name))
            # logger.info("For plan %s, current migrated VMs are %s out of total VMs %s",
            #     migration_plan.name, view.progress_card.migrated_vms(migration_plan.name),
            #     view.progress_card.total_vm_to_be_migrated(migration_plan.name))
            logger.info("For plan %s, is plan in progress: %s, time elapsed for migration: %s",
                migration_plan.name, view.progress_card.is_plan_visible(migration_plan.name),
                view.progress_card.get_clock(migration_plan.name))
        # return False if plan visible under "In Progress Plans"
        return not is_plan_visible

    # wait until plan is in progress
    wait_for(func=_get_plan_status, message="migration plan is in progress, be patient please",
     delay=5, num_sec=3600)

    view.migr_dropdown.item_select("Completed Plans")
    view.wait_displayed()
    logger.info("For plan %s, migration status after completion: %s, total time elapsed: %s",
        migration_plan.name, view.migration_plans_completed_list.get_vm_count_in_plan(
            migration_plan.name), view.migration_plans_completed_list.get_clock(
            migration_plan.name))
    assert view.migration_plans_completed_list.is_plan_succeeded(migration_plan.name)


@pytest.mark.parametrize('form_data_vm_obj_single_network', [['DPortGroup', 'ovirtmgmt',
                            dportgroup_template], ['VM Network', 'ovirtmgmt', rhel74_template]],
                        indirect=True)
def test_single_network_single_vm_migration(request, appliance, provider_setup, host_creds,
                                            conversion_tags,
                                            form_data_vm_obj_single_network):
    # This test will make use of migration request details page to track status of migration
    infrastructure_mapping_collection = appliance.collections.v2v_mappings

    mapping = infrastructure_mapping_collection.create(form_data_vm_obj_single_network[0])
    request.addfinalizer(lambda: infrastructure_mapping_collection.delete(mapping))

    migration_plan_collection = appliance.collections.v2v_plans
    migration_plan = migration_plan_collection.create(
        name="plan_{}".format(fauxfactory.gen_alphanumeric()), description="desc_{}"
        .format(fauxfactory.gen_alphanumeric()), infra_map=mapping.name,
        vm_list=form_data_vm_obj_single_network[1], start_migration=True)
    # as migration is started, try to track progress using migration plan request details page
    view = appliance.browser.create_view(navigator.get_class(migration_plan_collection, 'All').VIEW)
    wait_for(lambda: bool(view.progress_card.is_plan_started(migration_plan.name)),
        message="migration plan is starting, be patient please", delay=5, num_sec=150,
        handle_exception=True)
    view.progress_card.select_plan(migration_plan.name)
    view = appliance.browser.create_view(navigator.get_class(migration_plan_collection,
                                                             'Details').VIEW)
    view.wait_displayed()
    request_details_list = view.migration_request_details_list
    vm = request_details_list.read()[0]

    def _get_plan_status():
        clock_reading1 = request_details_list.get_clock(vm)
        time.sleep(1)  # wait 1 sec to see if clock is ticking
        logger.info("For vm %s, current message is %s", vm,
            request_details_list.get_message_text(vm))
        logger.info("For vm %s, current progress description is %s", vm,
            request_details_list.get_progress_description(vm))
        clock_reading2 = request_details_list.get_clock(vm)
        logger.info("clock_reading1: %s, clock_reading2:%s", clock_reading1, clock_reading2)
        logger.info("For vm %s, is currently in progress: %s", vm,
          request_details_list.is_in_progress(vm))
        return not(request_details_list.is_in_progress(vm) and (clock_reading1 < clock_reading2))

    wait_for(func=_get_plan_status, message="migration plan is in progress, be patient please",
     delay=5, num_sec=3600)
    assert (request_details_list.is_successful(vm) and not request_details_list.is_errored(vm))


@pytest.mark.parametrize(
    'form_data_dual_vm_obj_dual_datastore', [[['nfs', 'nfs',
    rhel74_template], ['iscsi', 'iscsi', rhel74_template]]],
    indirect=True
)
def test_dual_datastore_dual_vm_migration(request, appliance, provider_setup, host_creds,
                                        conversion_tags,
                                        form_data_dual_vm_obj_dual_datastore, soft_assert):
    # This test will make use of migration request details page to track status of migration
    infrastructure_mapping_collection = appliance.collections.v2v_mappings
    mapping = infrastructure_mapping_collection.create(form_data_dual_vm_obj_dual_datastore[0])
    request.addfinalizer(lambda: infrastructure_mapping_collection.delete(mapping))

    migration_plan_collection = appliance.collections.v2v_plans

    migration_plan = migration_plan_collection.create(
        name="plan_{}".format(fauxfactory.gen_alphanumeric()), description="desc_{}"
        .format(fauxfactory.gen_alphanumeric()), infra_map=mapping.name,
        vm_list=form_data_dual_vm_obj_dual_datastore[1], start_migration=True)
    # as migration is started, try to track progress using migration plan request details page
    view = appliance.browser.create_view(navigator.get_class(migration_plan_collection, 'All').VIEW)
    wait_for(lambda: bool(view.progress_card.is_plan_started(migration_plan.name)),
        message="migration plan is starting, be patient please", delay=5, num_sec=150,
        handle_exception=True)
    view.progress_card.select_plan(migration_plan.name)
    view = appliance.browser.create_view(navigator.get_class(migration_plan_collection,
                                                             'Details').VIEW)
    view.wait_displayed()
    request_details_list = view.migration_request_details_list
    vms = request_details_list.read()

    def _get_plan_status():
        migration_plan_in_progress_tracker = []
        for vm in vms:
            clock_reading1 = request_details_list.get_clock(vm)
            time.sleep(1)  # wait 1 sec to see if clock is ticking
            logger.info("For vm %s, current message is %s", vm,
                request_details_list.get_message_text(vm))
            logger.info("For vm %s, current progress description is %s", vm,
                request_details_list.get_progress_description(vm))
            clock_reading2 = request_details_list.get_clock(vm)
            logger.info("clock_reading1: %s, clock_reading2:%s", clock_reading1, clock_reading2)
            logger.info("For vm %s, is currently in progress: %s", vm,
              request_details_list.is_in_progress(vm))
            migration_plan_in_progress_tracker.append(request_details_list.is_in_progress(vm) and
              (clock_reading1 < clock_reading2))
        return not any(migration_plan_in_progress_tracker)

    wait_for(func=_get_plan_status, message="migration plan is in progress, be patient please",
     delay=5, num_sec=3600)

    for vm in vms:
        soft_assert(request_details_list.is_successful(vm) and
         not request_details_list.is_errored(vm))


@pytest.mark.parametrize(
    'form_data_vm_obj_dual_nics', [[['VM Network', 'ovirtmgmt'],
    ['DPortGroup', 'Storage - VLAN 33'], dual_network_template]],
    indirect=True
)
def test_dual_nics_migration(request, appliance, provider_setup, host_creds, conversion_tags,
         form_data_vm_obj_dual_nics):
    # TODO: Add "Delete" method call.This test case does not support update/delete
    # as update is not a supported feature for mapping,
    # and delete is not supported in our automation framework.
    infrastructure_mapping_collection = appliance.collections.v2v_mappings
    mapping = infrastructure_mapping_collection.create(form_data_vm_obj_dual_nics[0])
    request.addfinalizer(lambda: infrastructure_mapping_collection.delete(mapping))

    migration_plan_collection = appliance.collections.v2v_plans

    migration_plan = migration_plan_collection.create(
        name="plan_{}".format(fauxfactory.gen_alphanumeric()), description="desc_{}"
        .format(fauxfactory.gen_alphanumeric()), infra_map=mapping.name,
        vm_list=form_data_vm_obj_dual_nics[1], start_migration=True)

    # explicit wait for spinner of in-progress status card
    view = appliance.browser.create_view(navigator.get_class(migration_plan_collection, 'All').VIEW)
    wait_for(lambda: bool(view.progress_card.is_plan_started(migration_plan.name)),
        message="migration plan is starting, be patient please", delay=5, num_sec=150,
        handle_exception=True)

    def _get_plan_status():
        is_plan_visible = view.progress_card.is_plan_visible(migration_plan.name)
        if is_plan_visible:
            # log current status
            # uncomment following logs if github.com/ManageIQ/miq_v2v_ui_plugin/issues/415 fixed
            # logger.info("For plan %s, current migrated size is %s out of total size %s",
            #     migration_plan.name, view.progress_card.get_migrated_size(migration_plan.name),
            #     view.progress_card.get_total_size(migration_plan.name))
            # logger.info("For plan %s, current migrated VMs are %s out of total VMs %s",
            #     migration_plan.name, view.progress_card.migrated_vms(migration_plan.name),
            #     view.progress_card.total_vm_to_be_migrated(migration_plan.name))
            logger.info("For plan %s, is plan in progress: %s, time elapsed for migration: %s",
                migration_plan.name, view.progress_card.is_plan_visible(migration_plan.name),
                view.progress_card.get_clock(migration_plan.name))
        # return False if plan visible under "In Progress Plans"
        return not is_plan_visible

    # wait until plan is in progress
    wait_for(func=_get_plan_status, message="migration plan is in progress, be patient please",
     delay=5, num_sec=3600)

    view.migr_dropdown.item_select("Completed Plans")
    view.wait_displayed()
    logger.info("For plan %s, migration status after completion: %s, total time elapsed: %s",
        migration_plan.name, view.migration_plans_completed_list.get_vm_count_in_plan(
            migration_plan.name), view.migration_plans_completed_list.get_clock(
            migration_plan.name))
    assert view.migration_plans_completed_list.is_plan_succeeded(migration_plan.name)


@pytest.mark.parametrize('form_data_vm_obj_single_datastore', [['nfs', 'nfs', dual_disk_template]],
                        indirect=True)
def test_dual_disk_vm_migration(request, appliance, provider_setup, host_creds, conversion_tags,
                                form_data_vm_obj_single_datastore):
    infrastructure_mapping_collection = appliance.collections.v2v_mappings

    mapping = infrastructure_mapping_collection.create(form_data_vm_obj_single_datastore[0])
    request.addfinalizer(lambda: infrastructure_mapping_collection.delete(mapping))

    migration_plan_collection = appliance.collections.v2v_plans

    migration_plan = migration_plan_collection.create(
        name="plan_{}".format(fauxfactory.gen_alphanumeric()), description="desc_{}"
        .format(fauxfactory.gen_alphanumeric()), infra_map=mapping.name,
        vm_list=form_data_vm_obj_single_datastore[1], start_migration=True)
    # explicit wait for spinner of in-progress status card
    view = appliance.browser.create_view(navigator.get_class(migration_plan_collection, 'All').VIEW)
    wait_for(lambda: bool(view.progress_card.is_plan_started(migration_plan.name)),
        message="migration plan is starting, be patient please", delay=5, num_sec=150,
        handle_exception=True)

    def _get_plan_status():
        is_plan_visible = view.progress_card.is_plan_visible(migration_plan.name)
        if is_plan_visible:
            # log current status
            # uncomment following logs if github.com/ManageIQ/miq_v2v_ui_plugin/issues/415 fixed
            # logger.info("For plan %s, current migrated size is %s out of total size %s",
            #     migration_plan.name, view.progress_card.get_migrated_size(migration_plan.name),
            #     view.progress_card.get_total_size(migration_plan.name))
            # logger.info("For plan %s, current migrated VMs are %s out of total VMs %s",
            #     migration_plan.name, view.progress_card.migrated_vms(migration_plan.name),
            #     view.progress_card.total_vm_to_be_migrated(migration_plan.name))
            logger.info("For plan %s, is plan in progress: %s, time elapsed for migration: %s",
                migration_plan.name, view.progress_card.is_plan_visible(migration_plan.name),
                view.progress_card.get_clock(migration_plan.name))
        # return False if plan visible under "In Progress Plans"
        return not is_plan_visible

    # wait until plan is in progress
    wait_for(func=_get_plan_status, message="migration plan is in progress, be patient please",
     delay=5, num_sec=3600)

    view.migr_dropdown.item_select("Completed Plans")
    view.wait_displayed()
    logger.info("For plan %s, migration status after completion: %s, total time elapsed: %s",
        migration_plan.name, view.migration_plans_completed_list.get_vm_count_in_plan(
            migration_plan.name), view.migration_plans_completed_list.get_clock(
            migration_plan.name))
    assert view.migration_plans_completed_list.is_plan_succeeded(migration_plan.name)


@pytest.mark.parametrize('form_data_multiple_vm_obj_single_datastore', [['nfs', 'nfs',
                        [win7_template, win10_template]], ['nfs', 'nfs',
                        [win2016_template, rhel69_template]], ['nfs', 'nfs',
                        [win2012_template, ubuntu16_template]]], indirect=True)
def test_migrations_different_os_templates(request, appliance, provider_setup, host_creds,
                                    conversion_tags,
                                    form_data_multiple_vm_obj_single_datastore,
                                    soft_assert):
    infrastructure_mapping_collection = appliance.collections.v2v_mappings

    mapping = infrastructure_mapping_collection.create(
        form_data_multiple_vm_obj_single_datastore[0])
    request.addfinalizer(lambda: infrastructure_mapping_collection.delete(mapping))

    migration_plan_collection = appliance.collections.v2v_plans

    migration_plan = migration_plan_collection.create(
        name="plan_{}".format(fauxfactory.gen_alphanumeric()), description="desc_{}"
        .format(fauxfactory.gen_alphanumeric()), infra_map=mapping.name,
        vm_list=form_data_multiple_vm_obj_single_datastore[1], start_migration=True)
    # as migration is started, try to track progress using migration plan request details page
    view = appliance.browser.create_view(navigator.get_class(migration_plan_collection, 'All').VIEW)
    wait_for(lambda: bool(view.progress_card.is_plan_started(migration_plan.name)),
        message="migration plan is starting, be patient please", delay=5, num_sec=150,
        handle_exception=True)
    view.progress_card.select_plan(migration_plan.name)
    view = appliance.browser.create_view(navigator.get_class(migration_plan_collection,
                                                             'Details').VIEW)
    view.wait_displayed()
    request_details_list = view.migration_request_details_list
    vms = request_details_list.read()
    view.items_on_page.item_select('15')

    def _get_plan_status():
        migration_plan_in_progress_tracker = []
        for vm in vms:
            clock_reading1 = request_details_list.get_clock(vm)
            time.sleep(1)  # wait 1 sec to see if clock is ticking
            logger.info("For vm %s, current message is %s", vm,
                request_details_list.get_message_text(vm))
            logger.info("For vm %s, current progress description is %s", vm,
                request_details_list.get_progress_description(vm))
            clock_reading2 = request_details_list.get_clock(vm)
            logger.info("clock_reading1: %s, clock_reading2:%s", clock_reading1, clock_reading2)
            logger.info("For vm %s, is currently in progress: %s", vm,
              request_details_list.is_in_progress(vm))
            migration_plan_in_progress_tracker.append(request_details_list.is_in_progress(vm) and
              (clock_reading1 < clock_reading2))
        return not any(migration_plan_in_progress_tracker)

    wait_for(func=_get_plan_status, message="migration plan is in progress, be patient please",
     delay=5, num_sec=3600)

    for vm in vms:
        soft_assert(request_details_list.is_successful(vm) and
         not request_details_list.is_errored(vm))


@pytest.mark.parametrize('vm_list', ['NFS_Datastore_1', 'iSCSI_Datastore_1'], ids=['NFS', 'ISCSI'],
                         indirect=True)
@pytest.mark.parametrize('form_data_single_datastore', [['nfs', 'nfs']], indirect=True)
def test_end_to_end_migration(appliance, provider_setup, form_data_single_datastore,
                              vm_list):
    infrastructure_mapping_collection = appliance.collections.v2v_mappings
    mapping = infrastructure_mapping_collection.create(form_data_single_datastore)
    coll = appliance.collections.v2v_plans
    coll.create(name="plan_{}".format(fauxfactory.gen_alphanumeric()),
                description="desc_{}".format(fauxfactory.gen_alphanumeric()),
                infra_map=mapping.name,
                vm_list=vm_list,
                start_migration=True)
    view = appliance.browser.create_view(navigator.get_class(coll, 'All').VIEW)
    # explicit wait for spinner of in-progress status card
    wait_for(lambda: bool(view.progress_card.is_plan_started(coll.name)),
             message="migration plan is starting, be patient please", delay=5, num_sec=120)
    assert view._get_status(coll.name) == "Completed Plans"


def test_conversion_host_tags(appliance, provider_setup):
    """Tests following cases:

    1)Test Attribute in UI indicating host has/has not been configured as conversion host like Tags
    2)Test converstion host tags
    """
    tag1 = (appliance.collections.categories.instantiate(
            display_name='V2V - Transformation Host *')
            .collections.tags.instantiate(display_name='t'))

    tag2 = (appliance.collections.categories.instantiate(
            display_name='V2V - Transformation Method')
            .collections.tags.instantiate(display_name='VDDK'))

    host = provider_setup[1].hosts[0]
    # Remove any prior tags
    host.remove_tags(host.get_tags())

    host.add_tag(tag1)
    assert host.get_tags()[0].category.display_name in tag1.category.display_name
    host.remove_tag(tag1)

    host.add_tag(tag2)
    assert host.get_tags()[0].category.display_name in tag2.category.display_name
    host.remove_tag(tag2)

    host.remove_tags(host.get_tags())
