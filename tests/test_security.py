import pytest
from unittest.mock import MagicMock, patch
from core.security import SecurityManager, AutonomyMode


@pytest.fixture
def mock_config():
    """Fixture for a basic config."""
    return {
        "security": {
            "autonomy_mode": "manual",
            "require_confirmation": True,
        }
    }


@pytest.fixture
def security_manager(mock_config):
    """Fixture for SecurityManager with mocked logger."""
    with patch('core.security.setup_logger'):
        manager = SecurityManager(mock_config)
        # Mock require_confirmation to avoid interactive input
        manager.require_confirmation = MagicMock(return_value=True)
        return manager


class TestManualMode:
    def test_manual_mode_requires_confirmation(self):
        """MANUAL mode: whitelisted command still needs confirmation."""
        config = {"security": {"autonomy_mode": "manual"}}
        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)
            manager.whitelist = ["echo hello"]
            manager.require_confirmation = MagicMock(return_value=True)

            result = manager.can_execute_shell("echo hello")

            assert result is True
            manager.require_confirmation.assert_called_once()


class TestSemiAutoMode:
    def test_semi_auto_whitelisted_passes(self):
        """SEMI_AUTO mode: whitelisted command auto-passes without confirmation."""
        config = {"security": {"autonomy_mode": "semi_auto"}}
        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)
            manager.whitelist = ["echo hello"]
            manager.require_confirmation = MagicMock()

            result = manager.can_execute_shell("echo hello")

            assert result is True
            manager.require_confirmation.assert_not_called()

    def test_semi_auto_non_whitelisted_blocks(self):
        """SEMI_AUTO mode: non-whitelisted command needs confirmation."""
        config = {"security": {"autonomy_mode": "semi_auto"}}
        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)
            manager.whitelist = ["echo hello"]
            manager.require_confirmation = MagicMock(return_value=False)

            result = manager.can_execute_shell("ls -la")

            assert result is False
            manager.require_confirmation.assert_called_once()


class TestAutonomousMode:
    def test_autonomous_allows_non_dangerous(self):
        """AUTONOMOUS mode: any non-dangerous command auto-passes."""
        config = {"security": {"autonomy_mode": "autonomous"}}
        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)
            manager.require_confirmation = MagicMock()

            # Test a command not in whitelist
            result = manager.can_execute_shell("ls -la")

            assert result is True
            manager.require_confirmation.assert_not_called()

    def test_autonomous_whitelisted_also_passes(self):
        """AUTONOMOUS mode: whitelisted commands also pass."""
        config = {"security": {"autonomy_mode": "autonomous"}}
        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)
            manager.whitelist = ["echo hello"]
            manager.require_confirmation = MagicMock()

            result = manager.can_execute_shell("echo hello")

            assert result is True
            manager.require_confirmation.assert_not_called()


class TestDangerousCommandsBlocked:
    def test_dangerous_always_blocked_manual(self):
        """MANUAL mode: dangerous commands always blocked."""
        config = {"security": {"autonomy_mode": "manual"}}
        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)
            manager.require_confirmation = MagicMock()

            result = manager.can_execute_shell("rm -rf /")

            assert result is False
            manager.require_confirmation.assert_not_called()

    def test_dangerous_always_blocked_semi_auto(self):
        """SEMI_AUTO mode: dangerous commands always blocked."""
        config = {"security": {"autonomy_mode": "semi_auto"}}
        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)
            manager.require_confirmation = MagicMock()

            result = manager.can_execute_shell("rm -rf /")

            assert result is False
            manager.require_confirmation.assert_not_called()

    def test_dangerous_always_blocked_autonomous(self):
        """AUTONOMOUS mode: dangerous commands always blocked."""
        config = {"security": {"autonomy_mode": "autonomous"}}
        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)
            manager.require_confirmation = MagicMock()

            result = manager.can_execute_shell("rm -rf /")

            assert result is False
            manager.require_confirmation.assert_not_called()


class TestAutonomyModeManagement:
    def test_set_autonomy_mode(self):
        """Test setting autonomy mode."""
        config = {"security": {"autonomy_mode": "manual"}}
        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)
            assert manager.get_autonomy_mode() == AutonomyMode.MANUAL

            manager.set_autonomy_mode(AutonomyMode.AUTONOMOUS)
            assert manager.get_autonomy_mode() == AutonomyMode.AUTONOMOUS

    def test_invalid_autonomy_mode_defaults_to_manual(self):
        """Test that invalid autonomy mode defaults to MANUAL."""
        config = {"security": {"autonomy_mode": "invalid_mode"}}
        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)
            assert manager.get_autonomy_mode() == AutonomyMode.MANUAL


class TestEmptyCommandsBlocked:
    def test_empty_command_blocked(self):
        """Empty commands should be blocked in all modes."""
        for mode in ["manual", "semi_auto", "autonomous"]:
            config = {"security": {"autonomy_mode": mode}}
            with patch('core.security.setup_logger'):
                manager = SecurityManager(config)
                result = manager.can_execute_shell("")
                assert result is False

    def test_whitespace_only_command_blocked(self):
        """Whitespace-only commands should be blocked in all modes."""
        for mode in ["manual", "semi_auto", "autonomous"]:
            config = {"security": {"autonomy_mode": mode}}
            with patch('core.security.setup_logger'):
                manager = SecurityManager(config)
                result = manager.can_execute_shell("   ")
                assert result is False
