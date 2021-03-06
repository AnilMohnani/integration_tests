"""Manual tests"""
import pytest

from cfme import test_requirements

pytestmark = [test_requirements.quota, pytest.mark.manual]


@pytest.mark.tier(3)
@pytest.mark.manual('manualonly')
@pytest.mark.meta(coverage=[1456819])
def test_quota_for_simultaneous_service_catalog_request_with_different_users():
    """
    This test case is to test quota for simultaneous service catalog request with different users.

    Polarion:
        assignee: tpapaioa
        initialEstimate: 1/4h
        caseimportance: low
        caseposneg: positive
        testtype: functional
        startsin: 5.8
        casecomponent: Provisioning
        tags: quota
        testSteps:
            1. Create a service catalog with vm_name, instance_type &
               number_of_vms as fields.
            2. Set quotas threshold values for number_of_vms to 5
            3. Create two users from same group try to provision service catalog from different
               web-sessions with more that quota limit
        expectedResults:
            1.
            2.
            3. Quota exceeded message should be displayed

    Bugzilla:
        1456819

    """
    pass


@pytest.mark.tier(3)
@pytest.mark.meta(coverage=[1455844])
def test_service_template_provisioning_quota_for_number_of_vms_using_custom_dialog():
    """
    This test case is to test service template provisioning quota for number of vm's using custom
    dialog.

    Polarion:
        assignee: tpapaioa
        initialEstimate: 1/4h
        caseimportance: medium
        caseposneg: positive
        testtype: functional
        startsin: 5.8
        casecomponent: Provisioning
        tags: quota
        testSteps:
            1. Create a service catalog with vm_name, instance_type &
               number_of_vms as fields.
            2. Set quotas threshold values for number_of_vms to 5
            3. Provision service catalog with vm count as 10.
        expectedResults:
            1.
            2.
            3. CFME should show quota exceeded message for VMs requested

    Bugzilla:
        1455844
    """
    pass


@pytest.mark.tier(3)
@pytest.mark.meta(coverage=[1455844])
def test_quota_enforcement_for_cloud_volumes():
    """
    This test case is to test quota enforcement for cloud volumes

    Polarion:
        assignee: tpapaioa
        initialEstimate: 1/4h
        caseimportance: medium
        caseposneg: positive
        testtype: functional
        startsin: 5.8
        casecomponent: Provisioning
        tags: quota
        testSteps:
            1. Add openstack provider
            2. Set quota for storage
            3. While provisioning instance; add cloud volume with values
            4. Submit the request and see the last message in request info row
        expectedResults:
            1.
            2.
            3.
            4. Last message should show requested storage value is equal to
               instance type's default storage + volume storage value added while provisioning.

    Bugzilla:
        1455349
    """
    pass


@pytest.mark.tier(2)
@pytest.mark.manual('manualonly')
@pytest.mark.meta(coverage=[1531914, 1534589])
def test_quota_with_invalid_service_request():
    """
    This test case is to test quotas with various regions and invalid service requests
    To reproduce this issue: (You"ll need to have the RedHat Automate
    domain)

    Polarion:
        assignee: tpapaioa
        initialEstimate: 1/4h
        caseimportance: medium
        caseposneg: positive
        testtype: functional
        startsin: 5.9
        casecomponent: Control
        tags: quota
        testSteps:
            1. Setup multiple zones.(You can use a single appliance and just add a "test" zone)
            2. Add VMWare provider and configure it to the "test" zone.
            3. Create a VMWare Service Item.
            4. Order the Service.
            5. Delete the Service Template used in the Service creation in step 3.
            6. Modify the VMWare provider to use the default zone. (This should
               leave the existing Service request(s) in the queue for the "test" zone
               and the service_template will be invalid)
            7. Provision a VMWare VM.
        expectedResults:
            1.
            2.
            3.
            4.
            5.
            6. You should see the following error in the log:
               "[----] E, [2018-01-06T11:11:20.073924 #13027:e0ffc4] ERROR -- :
               Q-task_id([miq_provision_787]) MiqAeServiceModelBase.ar_method raised:
               <NoMethodError>: <undefined method `service_resources" for
               nil:NilClass> [----] E, [2018-01-06T11:11:20.074019 #13027:e0ffc4] ERROR -- :
               Q-task_id([miq_provision_787])"

    Bugzilla:
        1534589
        1531914
    """
    pass


@pytest.mark.tier(2)
def test_notification_show_notification_when_quota_is_exceed():
    """
    This test case is to check when quota is exceeded, CFME should notify with reason.

    Polarion:
        assignee: tpapaioa
        initialEstimate: 1/4h
        caseimportance: medium
        caseposneg: positive
        testtype: functional
        startsin: 5.8
        casecomponent: Services
        tags: quota
        testSteps:
            1. Add provider
            2. Set quota
            3. Provision VM via service or life cylce with more than quota assigned
        expectedResults:
            1.
            2.
            3. CFME should notify with reason why provision VM is denied
    """
    pass


@pytest.mark.tier(2)
@pytest.mark.meta(coverage=[1515979])
def test_orphaned_archived_vms_get_excluded_from_used_quota_counts():
    """Test that used Quota gets recounted and reduced, when a VM is
       orphaned/archived.

    Polarion:
        assignee: tpapaioa
        casecomponent: Infra
        caseimportance: medium
        initialEstimate: 1/6h
        testSteps:
            1. Setup Quota limits for tenant(My Company or create new tenant)
            2. Provision a VM and check quota denied message for used counts.
            3. Archive an active VM and repeat step 2.
            4. Notice the used counts are un-changes.
        expectedResults:
            1.
            2. 'Quota Exceed' message for VM provision request
            3. VM state should be changed to archived
            4. Orphaned/Archived VMs excluded in used count

    Bugzilla:
        1515979
    """
    pass
