# -*- coding: utf-8 -*-
"""Test for WebMKS Remote Consoles of VMware Providers."""
import imghdr
import socket

import pytest
from wait_for import wait_for

from cfme import test_requirements
from cfme.infrastructure.provider.virtualcenter import VMwareProvider
from cfme.markers.env_markers.provider import providers
from cfme.utils import ssh
from cfme.utils.conf import credentials
from cfme.utils.generators import random_vm_name
from cfme.utils.log import logger
from cfme.utils.net import wait_pingable
from cfme.utils.providers import ProviderFilter


pytestmark = [
    pytest.mark.usefixtures('setup_provider'),
    pytest.mark.provider(gen_func=providers,
                         filters=[ProviderFilter(classes=[VMwareProvider],
                                                 required_flags=['webmks_console'])],
                         scope='module'),
]


@pytest.fixture(scope="function")
def vm_obj(appliance, provider, setup_provider, console_template):
    """VM creation/deletion fixture.

    Create a VM on the provider with the given template, and return the vm_obj.

    Clean up VM when test is done.
    """
    vm_obj = appliance.collections.infra_vms.instantiate(random_vm_name('webmks'),
                                                         provider,
                                                         console_template.name)
    vm_obj.create_on_provider(timeout=2400, find_in_cfme=True, allow_skip="default")
    yield vm_obj

    vm_obj.cleanup_on_provider()


@pytest.fixture
def ssh_client(vm_obj, console_template):
    """Provide vm_ssh_client for ssh operations in the test."""
    console_vm_username = credentials.get(console_template.creds).username
    console_vm_password = credentials.get(console_template.creds).password
    wait_pingable(vm_obj.mgmt, allow_ipv6=False, wait=300)
    with ssh.SSHClient(hostname=vm_obj.ip_address, username=console_vm_username,
            password=console_vm_password) as vm_ssh_client:
        yield vm_ssh_client


@test_requirements.webmks
def test_webmks_vm_console(request, appliance, provider, vm_obj, configure_websocket,
        configure_console_webmks, take_screenshot, ssh_client):
    """Test the VMware WebMKS console support for a particular provider.

    The supported providers are:
        VMware vSphere6 and vSphere6.5

    For a given provider, and a given VM, the console will be opened, and then:

        - The console's status will be checked.
        - A command that creates a file will be sent through the console.
        - Using ssh we will check that the command worked (i.e. that the file
          was created.)

    Polarion:
        assignee: apagac
        casecomponent: Infra
        caseimportance: medium
        initialEstimate: 1/4h
    """
    console_vm_username = credentials[provider.data.templates.get('console_template')
                            ['creds']].get('username')
    console_vm_password = credentials[provider.data.templates.get('console_template')
                            ['creds']].get('password')

    vm_obj.open_console(console='VM Console', invokes_alert=True)
    assert vm_obj.vm_console, 'VMConsole object should be created'
    vm_console = vm_obj.vm_console

    request.addfinalizer(vm_console.close_console_window)
    request.addfinalizer(appliance.server.logout)
    try:
        assert vm_console.wait_for_connect(180), "VM Console did not reach 'connected' state"
        # Get the login screen image, and make sure it is a jpeg file:
        screen = vm_console.get_screen(180)
        assert imghdr.what('', screen) == 'jpeg'

        assert vm_console.wait_for_text(text_to_find="login:", timeout=200),\
            "VM Console didn't prompt for Login"

        def _get_user_count_before_login():
            try:
                result = ssh_client.run_command("who --count", ensure_user=True)
                return result.success, result
            except socket.error as e:
                if e.errno == socket.errno.ECONNRESET:
                    logger.exception("Socket Error Occured: [104] Connection Reset by peer.")
                logger.info("Trying again to perform 'who --count' over ssh.")
                return False

        result_before_login, _ = wait_for(func=_get_user_count_before_login,
                                timeout=300, delay=5)
        result_before_login = result_before_login[1]
        logger.info("Output of who --count is {} before login".format(result_before_login))
        # Enter Username:
        vm_console.send_keys(console_vm_username)
        # find only "Pass" as sometime tessaract reads "w" as "u" and fails
        assert vm_console.wait_for_text(text_to_find="Pass", timeout=200),\
            "VM Console didn't prompt for Password"
        # Enter Password:
        vm_console.send_keys("{}\n".format(console_vm_password))

        logger.info("Wait to get the '$' prompt")

        vm_console.wait_for_text(text_to_find=provider.data.templates.get('console_template')
            ['prompt_text'], timeout=200)

        def _validate_login():
            # the following try/except is required to handle the exception thrown by SSH
            # while connecting to VMware VM.It throws "[Error 104]Connection reset by Peer".
            try:
                result_after_login = ssh_client.run_command("who --count",
                                            ensure_user=True)
                logger.info("Output of 'who --count' is {} after login"
                .format(result_after_login))
                return (result_before_login.output.split('=')[1][0] <
                 result_after_login.output.split('=')[1][0])
            except socket.error as e:
                if e.errno == socket.errno.ECONNRESET:
                    logger.exception("Socket Error Occured: [104] Connection Reset by peer.")
                logger.info("Trying again to perform 'who --count' over ssh.")
                return False

        # Number of users before login would be 0 and after login would be 180
        # If below assertion would fail result_after_login is also 0,
        # denoting login failed
        wait_for(func=_validate_login, timeout=300, delay=5)

        # create file on system
        vm_console.send_keys("touch blather\n")
        vm_console.send_keys("\n\n")

        vm_console.send_ctrl_alt_delete()
        assert vm_console.wait_for_text(text_to_find="login:", timeout=200,
            to_disappear=True), (
            "Text 'login:' never disappeared, indicating failure"
            " of CTRL+ALT+DEL button functionality, please check if OS reboots on "
            "CTRL+ALT+DEL key combination and CTRL+ALT+DEL button on HTML5 Console is working.")
        assert vm_console.wait_for_text(text_to_find="login:", timeout=200), (
            "VM Console didn't prompt for Login")
        assert vm_console.send_fullscreen(), ("VM Console Toggle Full Screen button does not work")
        wait_pingable(vm_obj.mgmt, allow_ipv6=False, wait=300)
        wait_for(
            func=ssh_client.run_command,
            func_args=["ls blather"],
            func_kwargs={'ensure_user': True},
            handle_exception=True,
            fail_condition=lambda result: result.failed,  # rc != 0
            delay=1,
            num_sec=60
        )
        # if file was created in previous steps it will be removed here
        # we will get instance of SSHResult
        # Sometimes Openstack drops characters from word 'blather' hence try to remove
        # file using partial file name. Known issue, being worked on.
        command_result = ssh_client.run_command("rm blather", ensure_user=True)
        assert command_result

    except Exception:
        # Take a screenshot if an exception occurs
        vm_console.switch_to_console()
        take_screenshot("ConsoleScreenshot")
        vm_console.switch_to_appliance()
        raise


@pytest.mark.manual('manualonly')
@test_requirements.webmks
@pytest.mark.tier(2)
@pytest.mark.parametrize('browser', ['chrome_latest', 'firefox_latest'])
@pytest.mark.parametrize('operating_system', ['fedora_latest', 'rhel8.x', 'rhel7.x', 'rhel6.x'])
def test_webmks_console_linux(browser, operating_system, provider):
    """
    This testcase is here to reflect testing matrix for webmks consoles. Combinations listed
    are being tested manually. Originally, there was one testcase for every combination, this
    approach reduces number of needed testcases.

    Polarion:
        assignee: apagac
        casecomponent: Infra
        initialEstimate: 2h
        caseimportance: high
        setup:
            1. Login to CFME Appliance as admin.
            2. On top right click Administrator|EVM -> Configuration.
            3. Under VMware Console Support section and click on Dropdown in front
               of "Use" and select "VMware WebMKS".
            4. Click save at the bottom of the page.
               This will setup your appliance for using VMware WebMKS Console and not
               to use VMRC Plug in which is Default when you setup appliance.
            5. Provision a testing VM.
        testSteps:
            1. Navigate to testing VM
            2. Launch the console by Access -> VM Console
            3. Make sure the console accepts commands
            4. Make sure the characters are visible
        expectedResults:
            1. VM Details displayed
            2. Console launched
            3. Console accepts characters
            4. Characters not garbled; no visual defect
    """
    pass


@pytest.mark.manual('manualonly')
@test_requirements.webmks
@pytest.mark.tier(2)
@pytest.mark.parametrize('browser', ['edge', 'internet_explorer'])
@pytest.mark.parametrize('operating_system', ['windows7', 'windows10',
 'windows_server2012', 'windows_server2016'])
def test_webmks_console_windows(browser, operating_system, provider):
    """
    This testcase is here to reflect testing matrix for webmks consoles. Combinations listed
    are being tested manually. Originally, there was one testcase for every combination, this
    approach reduces number of needed testcases.

    Polarion:
        assignee: apagac
        casecomponent: Infra
        initialEstimate: 2h
        caseimportance: high
        setup:
            1. Login to CFME Appliance as admin.
            2. On top right click Administrator|EVM -> Configuration.
            3. Under VMware Console Support section and click on Dropdown in front
               of "Use" and select "VMware WebMKS".
            4. Click save at the bottom of the page.
               This will setup your appliance for using VMware WebMKS Console and not
               to use VMRC Plug in which is Default when you setup appliance.
            5. Provision a testing VM.
        testSteps:
            1. Navigate to testing VM
            2. Launch the console by Access -> VM Console
            3. Make sure the console accepts commands
            4. Make sure the characters are visible
        expectedResults:
            1. VM Details displayed
            2. Console launched
            3. Console accepts characters
            4. Characters not garbled; no visual defect
    """
    pass


@pytest.mark.manual('manualonly')
@test_requirements.webmks
@pytest.mark.tier(1)
def test_webmks_console_passwordwithspecialchars():
    """
    VMware WebMKS Remote Console Test; password with special characters

    Bugzilla:
        1545927

    Polarion:
        assignee: apagac
        casecomponent: Infra
        caseimportance: critical
        initialEstimate: 1/3h
        setup: On CFME Appliance do the following:
               1) Login to CFME Appliance as admin.
               2) On top right click Administrator|EVM -> Configuration.
               3) Under VMware Console Support section and click on Dropdown in front
               of "Use" and select "VMware WebMKS".
               4) Click save at the bottom of the page.
               This will setup your appliance for using VMware WebMKS Console and not
               to use VMRC Plug in which is Default when you setup appliance.
        startsin: 5.8
    """
    pass
