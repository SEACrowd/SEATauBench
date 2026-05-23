import pytest

from tau2.data_model.message import ToolCall
from tau2.domains.telecom.user_data_model import (
    APNNames,
    APNSettings,
    AppPermissions,
    AppStatus,
    MockPhoneAttributes,
    NetworkModePreference,
    NetworkStatus,
    NetworkTechnology,
    PerformanceLevel,
    SignalStrength,
    SimStatus,
    TelecomUserDB,
    UserSurroundings,
    VpnDetails,
)
from tau2.domains.telecom.user_tools import TelecomUserTools
from tau2.environment.environment import Environment


@pytest.fixture
def telecom_tools():
    """Fixture to create and return TelecomUserTools instance for testing."""
    device_attrs = MockPhoneAttributes()
    surroundings_attrs = UserSurroundings()
    db = TelecomUserDB(device=device_attrs, surroundings=surroundings_attrs)
    # Initialize with some default apps for testing app-related tools
    db.device.app_statuses = {
        "messaging": AppStatus(app_name="messaging", permissions=AppPermissions()),
        "browser": AppStatus(
            app_name="browser", permissions=AppPermissions(network=True, storage=True)
        ),
    }
    tools = TelecomUserTools(db=db)
    return tools


class TestTelecomUserTools:
    def test_check_status_bar_default(self, telecom_tools: TelecomUserTools):
        status = telecom_tools.check_status_bar()
        assert (
            status["status_bar"]["battery_level"] == telecom_tools.device.battery_level
        )
        assert status["status_bar"]["mobile_data_enabled"] is True

    def test_check_status_bar_airplane_mode(self, telecom_tools: TelecomUserTools):
        telecom_tools.device.airplane_mode = True
        status = telecom_tools.check_status_bar()
        assert status["status_bar"]["airplane_mode"] is True
        assert (
            status["status_bar"]["battery_level"] == telecom_tools.device.battery_level
        )

    def test_toggle_airplane_mode(self, telecom_tools: TelecomUserTools):
        initial_state = telecom_tools.device.airplane_mode
        result = telecom_tools.toggle_airplane_mode()

        assert result["success"] is True
        assert result["airplane_mode"] is (not initial_state)
        assert telecom_tools.device.airplane_mode is not initial_state

        # Toggle back
        telecom_tools.toggle_airplane_mode()
        assert telecom_tools.device.airplane_mode is initial_state

    def test_turn_airplane_mode_on_off(self, telecom_tools: TelecomUserTools):
        telecom_tools.turn_airplane_mode_on()
        assert telecom_tools.device.airplane_mode is True
        status = telecom_tools.check_status_bar()
        assert status["status_bar"]["airplane_mode"] is True

        telecom_tools.turn_airplane_mode_off()
        assert telecom_tools.device.airplane_mode is False
        status = telecom_tools.check_status_bar()
        assert status["status_bar"]["airplane_mode"] is False

    def test_check_network_status(self, telecom_tools: TelecomUserTools):
        status = telecom_tools.check_network_status()
        assert status["airplane_mode"] is False
        assert status["sim_status"] == telecom_tools.device.sim_card_status.value
        assert (
            status["cellular_signal"]
            == telecom_tools.device.network_signal_strength.value
        )

    def test_check_sim_status(self, telecom_tools: TelecomUserTools):
        telecom_tools.device.sim_card_status = SimStatus.ACTIVE
        assert telecom_tools.check_sim_status()["sim_status"] == SimStatus.ACTIVE.value

        telecom_tools.device.sim_card_missing = True
        assert telecom_tools.check_sim_status()["sim_status"] == SimStatus.MISSING.value
        telecom_tools.device.sim_card_missing = False

        telecom_tools.device.sim_card_status = SimStatus.LOCKED_PIN
        assert (
            telecom_tools.check_sim_status()["sim_status"] == SimStatus.LOCKED_PIN.value
        )

    def test_reseat_sim_card(self, telecom_tools: TelecomUserTools):
        telecom_tools.unseat_sim_card()
        assert telecom_tools._check_sim_status() == SimStatus.MISSING
        telecom_tools.reseat_sim_card()
        assert telecom_tools._check_sim_status() != SimStatus.MISSING
        # Assuming reseating triggers a network search and connects if possible
        assert telecom_tools.device.network_connection_status == NetworkStatus.CONNECTED

    def test_toggle_data(self, telecom_tools: TelecomUserTools):
        initial_data_state = telecom_tools.device.data_enabled
        result = telecom_tools.toggle_data()
        assert telecom_tools.device.data_enabled is not initial_data_state
        assert result["mobile_data_enabled"] is (not initial_data_state)

    def test_toggle_roaming(self, telecom_tools: TelecomUserTools):
        initial_roaming_state = telecom_tools.device.roaming_enabled
        result = telecom_tools.toggle_roaming()
        assert telecom_tools.device.roaming_enabled is not initial_roaming_state
        assert result["data_roaming_enabled"] is (not initial_roaming_state)

    def test_set_network_mode_preference(self, telecom_tools: TelecomUserTools):
        result = telecom_tools.set_network_mode_preference(
            NetworkModePreference.FOUR_G_ONLY
        )
        assert result["success"] is True
        assert (
            result["network_mode_preference"] == NetworkModePreference.FOUR_G_ONLY.value
        )
        assert (
            telecom_tools.device.network_mode_preference
            == NetworkModePreference.FOUR_G_ONLY
        )
        # Check if network search simulates a change (simplified check)
        assert (
            telecom_tools.device.network_technology_connected
            == NetworkTechnology.FOUR_G
        )

        result = telecom_tools.set_network_mode_preference("invalid_mode")
        assert result["success"] is False
        assert result["error_code"] == "invalid_network_mode"

    def test_check_apn_settings(self, telecom_tools: TelecomUserTools):
        default_apn = APNSettings()
        telecom_tools.device.active_apn_settings = default_apn
        settings = telecom_tools.check_apn_settings()
        assert settings["apn_name"] == default_apn.apn_name.value
        assert settings["mmsc_url"] == default_apn.mmsc_url

    def test_set_apn_settings(self, telecom_tools: TelecomUserTools):
        # Test setting APN with APNSettings object
        new_apn = APNSettings(
            apn_name=APNNames.INTERNET,
            mmsc_url="http://mms.new.com",
            mms_apn="mms",
            reset_at_reboot=False,
        )
        result = telecom_tools.set_apn_settings(new_apn)
        assert result["success"] is True
        assert result["apn_name"] == APNNames.INTERNET.value
        assert "status_bar" in result
        assert telecom_tools.device.active_apn_settings.apn_name == APNNames.INTERNET
        assert telecom_tools.device.active_apn_settings.mmsc_url == "http://mms.new.com"
        # Network search should be triggered
        assert telecom_tools.device.network_connection_status == NetworkStatus.CONNECTED

        # Test setting APN with dict
        result = telecom_tools.set_apn_settings(
            {
                "apn_name": APNNames.INTERNET,
                "mmsc_url": "http://mms.new.com",
                "mms_apn": "mms",
                "reset_at_reboot": False,
            }
        )
        assert result["success"] is True
        assert result["apn_name"] == APNNames.INTERNET.value
        assert "status_bar" in result
        assert telecom_tools.device.active_apn_settings.apn_name == APNNames.INTERNET
        # Network search should be triggered again
        assert telecom_tools.device.network_connection_status == NetworkStatus.CONNECTED

    def test_reset_apn_settings(self, telecom_tools: TelecomUserTools):
        # Set custom APN settings
        custom_apn = APNSettings(
            apn_name=APNNames.INTERNET,
            mmsc_url="http://mms.new.com",
            mms_apn="mms",
            reset_at_reboot=False,
        )
        telecom_tools.device.active_apn_settings = custom_apn
        assert telecom_tools.device.active_apn_settings.apn_name == APNNames.INTERNET
        assert not telecom_tools.device.active_apn_settings.reset_at_reboot

        # Call reset_apn_settings
        result = telecom_tools.reset_apn_settings()
        assert result["success"] is True
        assert result["reset_at_reboot"] is True
        assert telecom_tools.device.active_apn_settings.reset_at_reboot is True
        # APN settings should not be reset yet
        assert telecom_tools.device.active_apn_settings.apn_name == APNNames.INTERNET

        # Now reboot to trigger the actual reset
        telecom_tools.reboot_device()
        assert (
            telecom_tools.device.active_apn_settings.apn_name == APNNames.INTERNET
        )  # Default APN name
        assert not telecom_tools.device.active_apn_settings.reset_at_reboot

    def test_check_wifi_status(self, telecom_tools: TelecomUserTools):
        telecom_tools.device.wifi_enabled = False
        assert telecom_tools.check_wifi_status()["wifi_enabled"] is False

        telecom_tools.device.wifi_enabled = True
        telecom_tools.device.wifi_connected = False
        wifi_status = telecom_tools.check_wifi_status()
        assert wifi_status["wifi_enabled"] is True
        assert wifi_status["wifi_connected"] is False

        telecom_tools.device.wifi_connected = True
        telecom_tools.device.wifi_ssid = "MyHomeWiFi"
        telecom_tools.device.wifi_signal_strength = SignalStrength.GOOD
        status = telecom_tools.check_wifi_status()
        assert status["wifi_connected"] is True
        assert status["wifi_ssid"] == "MyHomeWiFi"
        assert status["wifi_signal_strength"] == SignalStrength.GOOD.value

    def test_toggle_wifi(self, telecom_tools: TelecomUserTools):
        telecom_tools.device.airplane_mode = False  # Ensure wifi can be toggled
        initial_wifi_state = telecom_tools.device.wifi_enabled
        result = telecom_tools.toggle_wifi()
        assert telecom_tools.device.wifi_enabled is not initial_wifi_state
        assert result["success"] is True
        assert result["wifi_enabled"] is (not initial_wifi_state)

        # Test when airplane mode is ON
        telecom_tools.device.airplane_mode = True
        telecom_tools.device.wifi_enabled = False  # Try to toggle wifi on
        result = telecom_tools.toggle_wifi()
        assert result["success"] is False
        assert result["error_code"] == "airplane_mode_on"
        assert telecom_tools.device.wifi_enabled is False  # State should not change

    def test_check_vpn_status(self, telecom_tools: TelecomUserTools):
        telecom_tools.device.vpn_enabled_setting = False
        telecom_tools.device.vpn_connected = False
        vpn_status = telecom_tools.check_vpn_status()
        assert vpn_status["enabled_setting"] is False
        assert vpn_status["connected"] is False

        telecom_tools.device.vpn_enabled_setting = True
        vpn_status = telecom_tools.check_vpn_status()
        assert vpn_status["enabled_setting"] is True
        assert vpn_status["connected"] is False

        telecom_tools.device.vpn_connected = True
        telecom_tools.device.vpn_details = VpnDetails(
            server_address="1.2.3.4", protocol="TestVPN"
        )
        status = telecom_tools.check_vpn_status()
        assert status["connected"] is True
        assert status["details"]["server_address"] == "1.2.3.4"

    def test_connect_disconnect_vpn(self, telecom_tools: TelecomUserTools):
        # Connect VPN
        telecom_tools.device.vpn_enabled_setting = True  # Assume setting is on
        result = telecom_tools.connect_vpn()
        assert result["success"] is True
        assert result["vpn_connected"] is True
        assert telecom_tools.device.vpn_connected is True
        assert telecom_tools.device.vpn_details is not None
        assert (
            telecom_tools.device.vpn_details.server_address
            == telecom_tools.default_vpn_details.server_address
        )

        # Try connecting again
        result = telecom_tools.connect_vpn()
        assert result["success"] is True
        assert result["vpn_connected"] is True

        # Disconnect VPN
        result = telecom_tools.disconnect_vpn()
        assert result["success"] is True
        assert result["vpn_connected"] is False
        assert telecom_tools.device.vpn_connected is False
        assert telecom_tools.device.vpn_details is None

        # Try disconnecting again
        result = telecom_tools.disconnect_vpn()
        assert result["success"] is False
        assert result["error_code"] == "no_active_vpn"

    def test_check_installed_apps(self, telecom_tools: TelecomUserTools):
        apps = telecom_tools.check_installed_apps()
        assert "messaging" in apps["installed_apps"]
        assert "browser" in apps["installed_apps"]

    def test_check_app_status(self, telecom_tools: TelecomUserTools):
        status = telecom_tools.check_app_status("messaging")
        assert status["found"] is True
        assert status["app_name"] == "messaging"
        assert status["allowed_permissions"] == []

        status = telecom_tools.check_app_status("browser")
        assert "network" in status["allowed_permissions"]

        status = telecom_tools.check_app_status("nonexistent_app")
        assert status["found"] is False
        assert status["app_name"] == "nonexistent_app"

    def test_check_app_permissions(self, telecom_tools: TelecomUserTools):
        permissions = telecom_tools.check_app_permissions("messaging")
        assert permissions["found"] is True
        assert permissions["allowed_permissions"] == []

        telecom_tools.device.app_statuses["messaging"].permissions.storage = True
        permissions = telecom_tools.check_app_permissions("messaging")
        assert permissions["allowed_permissions"] == ["storage"]

    def test_grant_app_permission(self, telecom_tools: TelecomUserTools):
        app_name = "messaging"
        permission = "storage"

        assert telecom_tools.device.app_statuses[app_name].permissions.storage is False
        result = telecom_tools.grant_app_permission(app_name, permission)
        assert result["success"] is True
        assert result["permission"] == permission
        assert telecom_tools.device.app_statuses[app_name].permissions.storage is True

        result = telecom_tools.grant_app_permission(app_name, "invalid_permission")
        assert result["success"] is False
        assert result["error_code"] == "invalid_permission"

        result = telecom_tools.grant_app_permission("nonexistent_app", permission)
        assert result["success"] is False
        assert result["error_code"] == "app_not_found"

    def test_remove_app_permission(self, telecom_tools: TelecomUserTools):
        app_name = "browser"  # browser has network=True by default in fixture
        permission_to_remove = "network"

        assert telecom_tools.device.app_statuses[app_name].permissions.network is True
        success, message = telecom_tools.remove_app_permission(
            app_name, permission_to_remove
        )
        assert success is True
        assert (
            f"Permission '{permission_to_remove}' removed from app '{app_name}'"
            in message
        )
        assert telecom_tools.device.app_statuses[app_name].permissions.network is False

        telecom_tools.device.app_statuses[app_name].permissions.storage = False
        # Try removing a permission that is already false
        success, message = telecom_tools.remove_app_permission(
            app_name, "storage"
        )  # storage is False
        assert success is True
        assert telecom_tools.device.app_statuses[app_name].permissions.storage is False

    def test_reboot_device(self, telecom_tools: TelecomUserTools):
        # Test APN reset functionality
        telecom_tools.device.active_apn_settings.reset_at_reboot = True
        telecom_tools.device.active_apn_settings.apn_name = APNNames.INTERNET
        result = telecom_tools.reboot_device()
        assert result["apn_reset"] is True
        assert (
            telecom_tools.device.active_apn_settings.apn_name == APNNames.INTERNET
        )  # Default APN name
        assert not telecom_tools.device.active_apn_settings.reset_at_reboot

        # Test network service restart
        telecom_tools.device.network_connection_status = NetworkStatus.CONNECTED
        telecom_tools.device.network_technology_connected = NetworkTechnology.FOUR_G
        telecom_tools.device.network_signal_strength = SignalStrength.GOOD

        result = telecom_tools.reboot_device()
        assert result["network_restarted"] is True
        assert telecom_tools.device.network_connection_status == NetworkStatus.CONNECTED

    def test_can_send_mms(self, telecom_tools: TelecomUserTools):
        # Setup for successful MMS
        telecom_tools.device.network_connection_status = NetworkStatus.CONNECTED
        telecom_tools.device.data_enabled = True
        telecom_tools.surroundings.mobile_data_usage_exceeded = False
        telecom_tools.device.network_technology_connected = NetworkTechnology.FOUR_G
        telecom_tools.device.wifi_calling_enabled = False
        telecom_tools.device.active_apn_settings.mmsc_url = "http://mms.example.com"
        telecom_tools.device.app_statuses["messaging"].permissions.sms = True
        telecom_tools.device.app_statuses["messaging"].permissions.storage = True
        assert telecom_tools.can_send_mms()["can_send_mms"] is True

        # Test various failure conditions
        telecom_tools.device.network_connection_status = NetworkStatus.NO_SERVICE
        assert telecom_tools.can_send_mms()["can_send_mms"] is False
        telecom_tools.device.network_connection_status = (
            NetworkStatus.CONNECTED
        )  # Reset

        telecom_tools.device.data_enabled = False
        assert telecom_tools.can_send_mms()["can_send_mms"] is False
        telecom_tools.device.data_enabled = True  # Reset

        telecom_tools.surroundings.mobile_data_usage_exceeded = True
        assert telecom_tools.can_send_mms()["can_send_mms"] is False
        telecom_tools.surroundings.mobile_data_usage_exceeded = False  # Reset

        telecom_tools.device.network_technology_connected = NetworkTechnology.TWO_G
        assert telecom_tools.can_send_mms()["can_send_mms"] is False
        telecom_tools.device.network_technology_connected = (
            NetworkTechnology.FOUR_G
        )  # Reset

        telecom_tools.device.wifi_calling_enabled = True
        telecom_tools.device.wifi_calling_mms_over_wifi = (
            True  # Carrier does not support
        )
        assert telecom_tools.can_send_mms()["can_send_mms"] is False
        telecom_tools.device.wifi_calling_enabled = False  # Reset

        telecom_tools.device.active_apn_settings.mmsc_url = None
        assert telecom_tools.can_send_mms()["can_send_mms"] is False
        telecom_tools.device.active_apn_settings.mmsc_url = (
            "http://mms.example.com"  # Reset
        )

        telecom_tools.device.app_statuses["messaging"].permissions.sms = False
        assert telecom_tools.can_send_mms()["can_send_mms"] is False

    def test_vpn_state_not_shared_across_instances(self):
        """Regression test for issue #154."""

        def make_tools():
            db = TelecomUserDB(
                device=MockPhoneAttributes(), surroundings=UserSurroundings()
            )
            return TelecomUserTools(db=db)

        sim1 = make_tools()
        sim2 = make_tools()

        sim1._connect_vpn()
        sim1.break_vpn()
        assert sim1.device.vpn_details.server_performance == PerformanceLevel.POOR

        sim2._connect_vpn()
        assert sim2.device.vpn_details.server_performance == PerformanceLevel.EXCELLENT

        assert (
            TelecomUserTools.default_vpn_details.server_performance
            == PerformanceLevel.EXCELLENT
        )

    def test_run_speed_test(self, telecom_tools: TelecomUserTools):
        # Basic connected state
        telecom_tools.device.airplane_mode = False
        telecom_tools.device.network_signal_strength = SignalStrength.GOOD
        telecom_tools.device.network_connection_status = NetworkStatus.CONNECTED
        telecom_tools.device.data_enabled = True
        telecom_tools.surroundings.mobile_data_usage_exceeded = False
        telecom_tools.device.network_technology_connected = NetworkTechnology.FOUR_G
        telecom_tools.device.data_saver_mode = False
        telecom_tools.device.vpn_connected = False

        result = telecom_tools.run_speed_test()
        assert result["success"] is True
        assert result["speed_mbps"] is not None
        assert result["performance"] == PerformanceLevel.GOOD.value

        # No connection
        telecom_tools.device.network_signal_strength = SignalStrength.NONE
        result = telecom_tools.run_speed_test()
        assert result["success"] is False
        assert result["error_code"] == "no_connection"
        telecom_tools.device.network_signal_strength = SignalStrength.GOOD  # Reset

        # Data saver mode
        telecom_tools.device.data_saver_mode = True
        result = telecom_tools.run_speed_test()
        # Speed should be lower, potentially affecting description
        # This needs careful checking based on the _run_speed_test logic
        assert result["success"] is True
        assert result["speed_mbps"] is not None
        telecom_tools.device.data_saver_mode = False  # Reset

        # Poor VPN
        telecom_tools.device.vpn_connected = True
        telecom_tools.device.vpn_details = VpnDetails(
            server_performance=PerformanceLevel.POOR
        )
        result = telecom_tools.run_speed_test()
        assert result["success"] is True
        assert result["speed_mbps"] is not None
        telecom_tools.device.vpn_connected = False  # Reset

        # 5G Excellent
        telecom_tools.device.network_technology_connected = NetworkTechnology.FIVE_G
        telecom_tools.device.network_signal_strength = SignalStrength.EXCELLENT
        result = telecom_tools.run_speed_test()
        assert result["performance"] == PerformanceLevel.EXCELLENT.value

    def test_environment_serializes_user_tool_payload_as_structured_json(
        self, telecom_tools: TelecomUserTools
    ):
        env = Environment(
            domain_name="telecom",
            policy="",
            tools=telecom_tools,
        )

        response = env.get_response(
            ToolCall(
                id="call-1",
                name="check_status_bar",
                arguments={},
                requestor="assistant",
            )
        )

        assert response.error is False
        assert "Status Bar:" not in response.content
        assert '"status_bar"' in response.content
        assert '"battery_level": 80' in response.content
