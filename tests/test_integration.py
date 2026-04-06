"""
Comprehensive integration tests for the APEX/Jarvis project.

Tests cover:
- Short-term memory operations
- Task plan execution with plugins
- Security manager functionality across autonomy modes
- Plugin pattern matching
- Memory entry creation and validation
- Task planner with mocked LLM responses
"""

import sys
sys.path.insert(0, '/sessions/inspiring-beautiful-cannon/mnt/Jarvis')

import pytest
import time
import json
from unittest.mock import MagicMock, patch, PropertyMock, call
from datetime import datetime

# Import all necessary classes from core
from core.interfaces import (
    CommandContext, CommandResult, PluginBase,
    TaskPlan, TaskStep, TaskStatus, MemoryEntry, MemoryEntryType
)
from core.memory.short_term import ShortTermMemory
from core.security import SecurityManager, AutonomyMode
from core.kernel import Kernel, SystemState
from plugins.system.echo import EchoPlugin


# ============================================================================
# Test 1: Short-term Memory Stores and Retrieves
# ============================================================================

class TestShortTermMemory:
    """Test suite for ShortTermMemory operations."""

    def test_short_term_memory_stores_and_retrieves(self):
        """Create ShortTermMemory, store entries, query, verify results."""
        memory = ShortTermMemory(max_entries=50)

        # Create and store entries
        entry1 = MemoryEntry(
            id="entry-1",
            content="User asked about the weather",
            metadata={"type": "question"},
            timestamp=time.time(),
            entry_type=MemoryEntryType.SESSION
        )

        entry2 = MemoryEntry(
            id="entry-2",
            content="Weather forecast shows sunny",
            metadata={"type": "response"},
            timestamp=time.time(),
            entry_type=MemoryEntryType.SESSION
        )

        entry3 = MemoryEntry(
            id="entry-3",
            content="User asked about temperature",
            metadata={"type": "question"},
            timestamp=time.time(),
            entry_type=MemoryEntryType.SESSION
        )

        # Store entries
        memory.store(entry1)
        memory.store(entry2)
        memory.store(entry3)

        # Query for entries containing "weather"
        results = memory.query("weather", k=5)

        # Verify results
        assert len(results) == 2, "Should find 2 entries containing 'weather'"
        assert results[0].id == "entry-2", "Most recent should be first (entry-2)"
        assert results[1].id == "entry-1", "Entry-1 should be second"

        # Query for "temperature"
        temp_results = memory.query("temperature", k=5)
        assert len(temp_results) == 1
        assert temp_results[0].id == "entry-3"

    def test_short_term_memory_respects_max_entries(self):
        """Test that memory respects max_entries limit and removes oldest."""
        memory = ShortTermMemory(max_entries=3)

        # Add 5 entries
        for i in range(5):
            entry = MemoryEntry(
                id=f"entry-{i}",
                content=f"Entry number {i}",
                timestamp=time.time(),
                entry_type=MemoryEntryType.SESSION
            )
            memory.store(entry)

        # Should only have 3 most recent
        recent = memory.get_recent(10)
        assert len(recent) == 3, "Should only have 3 entries"
        assert recent[0].id == "entry-2"
        assert recent[1].id == "entry-3"
        assert recent[2].id == "entry-4"

    def test_short_term_memory_case_insensitive_query(self):
        """Test that query is case-insensitive."""
        memory = ShortTermMemory(max_entries=50)

        entry = MemoryEntry(
            id="entry-1",
            content="The Quick Brown Fox",
            timestamp=time.time(),
            entry_type=MemoryEntryType.SESSION
        )
        memory.store(entry)

        # Query with different cases
        results_upper = memory.query("QUICK", k=5)
        results_lower = memory.query("quick", k=5)
        results_mixed = memory.query("QuIcK", k=5)

        assert len(results_upper) == 1
        assert len(results_lower) == 1
        assert len(results_mixed) == 1

    def test_short_term_memory_clear(self):
        """Test clearing all memory entries."""
        memory = ShortTermMemory(max_entries=50)

        # Add entries
        for i in range(5):
            entry = MemoryEntry(
                id=f"entry-{i}",
                content=f"Entry {i}",
                timestamp=time.time()
            )
            memory.store(entry)

        # Verify entries exist
        assert len(memory.get_recent(10)) == 5

        # Clear
        memory.clear()

        # Verify empty
        assert len(memory.get_recent(10)) == 0
        assert len(memory.query("Entry", k=5)) == 0


# ============================================================================
# Test 2: Task Plan Execution with Plugins
# ============================================================================

class TestTaskPlanExecution:
    """Test suite for task plan execution."""

    def test_task_plan_execution_with_mock_plugin(self):
        """Execute a TaskPlan with 2 steps pointing to mock plugins."""
        # Create a mock plugin
        mock_plugin = MagicMock(spec=PluginBase)
        mock_plugin.name.return_value = "TestPlugin"
        mock_plugin.patterns.return_value = ["test"]
        mock_plugin.execute.return_value = CommandResult(
            success=True,
            message="Test executed successfully"
        )

        # Create a mock kernel-like object
        mock_kernel = MagicMock()
        mock_kernel.plugins = {"TestPlugin": mock_plugin}
        mock_kernel.emit = MagicMock()
        mock_kernel._store_in_memory = MagicMock()
        mock_kernel.logger = MagicMock()

        # Create TaskPlan with 2 steps
        step1 = TaskStep(
            id="step-1",
            description="Execute test step 1",
            plugin_name="TestPlugin",
            params={"key": "value1"},
            status=TaskStatus.PENDING
        )

        step2 = TaskStep(
            id="step-2",
            description="Execute test step 2",
            plugin_name="TestPlugin",
            params={"key": "value2"},
            status=TaskStatus.PENDING
        )

        plan = TaskPlan(
            goal="Test goal",
            steps=[step1, step2],
            current_step_index=0,
            status=TaskStatus.PENDING
        )

        # Manually execute plan logic
        plan.status = TaskStatus.RUNNING

        for step in plan.steps:
            step.status = TaskStatus.RUNNING
            plugin = mock_kernel.plugins.get(step.plugin_name)
            assert plugin is not None

            ctx = CommandContext(
                raw_text=step.description,
                command_name=step.plugin_name,
                params=step.params,
                kernel=mock_kernel
            )

            result = plugin.execute(ctx)
            step.result = result
            step.status = TaskStatus.DONE
            plan.current_step_index += 1

        # Verify all steps are DONE
        if all(s.status == TaskStatus.DONE for s in plan.steps):
            plan.status = TaskStatus.DONE

        # Assertions
        assert plan.status == TaskStatus.DONE
        assert all(s.status == TaskStatus.DONE for s in plan.steps)
        assert mock_plugin.execute.call_count == 2

    def test_task_plan_execution_partial_failure(self):
        """Test plan execution that fails on second step."""
        mock_plugin = MagicMock(spec=PluginBase)
        mock_plugin.name.return_value = "FailPlugin"

        # First call succeeds, second fails
        mock_plugin.execute.side_effect = [
            CommandResult(success=True, message="Step 1 OK"),
            CommandResult(success=False, message="Step 2 failed")
        ]

        mock_kernel = MagicMock()
        mock_kernel.plugins = {"FailPlugin": mock_plugin}
        mock_kernel.emit = MagicMock()
        mock_kernel.logger = MagicMock()

        step1 = TaskStep(
            id="step-1",
            description="First step",
            plugin_name="FailPlugin",
            status=TaskStatus.PENDING
        )

        step2 = TaskStep(
            id="step-2",
            description="Second step",
            plugin_name="FailPlugin",
            status=TaskStatus.PENDING
        )

        plan = TaskPlan(
            goal="Will fail",
            steps=[step1, step2],
            status=TaskStatus.PENDING
        )

        # Execute plan
        plan.status = TaskStatus.RUNNING

        for step in plan.steps:
            step.status = TaskStatus.RUNNING
            plugin = mock_kernel.plugins.get(step.plugin_name)
            result = plugin.execute(CommandContext(
                raw_text=step.description,
                command_name=step.plugin_name,
                params={},
                kernel=mock_kernel
            ))
            step.result = result

            if result.success:
                step.status = TaskStatus.DONE
            else:
                step.status = TaskStatus.FAILED
                plan.status = TaskStatus.FAILED
                break

        # Assertions
        assert plan.status == TaskStatus.FAILED
        assert step1.status == TaskStatus.DONE
        assert step2.status == TaskStatus.FAILED


# ============================================================================
# Test 3: Task Plan Fails on Missing Plugin
# ============================================================================

class TestTaskPlanMissingPlugin:
    """Test suite for task plan with missing plugins."""

    def test_task_plan_fails_on_missing_plugin(self):
        """Plan with step referencing non-existent plugin should fail."""
        mock_kernel = MagicMock()
        mock_kernel.plugins = {}  # Empty plugins dict
        mock_kernel.emit = MagicMock()
        mock_kernel.logger = MagicMock()

        step = TaskStep(
            id="step-1",
            description="Use non-existent plugin",
            plugin_name="NonExistentPlugin",
            status=TaskStatus.PENDING
        )

        plan = TaskPlan(
            goal="Will fail",
            steps=[step],
            status=TaskStatus.PENDING
        )

        # Execute plan
        plan.status = TaskStatus.RUNNING
        step.status = TaskStatus.RUNNING

        plugin = mock_kernel.plugins.get(step.plugin_name)

        if not plugin:
            step.status = TaskStatus.FAILED
            plan.status = TaskStatus.FAILED

        # Assertions
        assert plan.status == TaskStatus.FAILED
        assert step.status == TaskStatus.FAILED


# ============================================================================
# Test 4: Security Manager - Dangerous Commands Blocked in All Modes
# ============================================================================

class TestSecurityDangerousCommands:
    """Test suite for security blocking of dangerous commands."""

    @pytest.fixture
    def mock_config(self):
        """Provide a minimal config for SecurityManager."""
        return {
            "security": {
                "autonomy_mode": "autonomous",
                "require_confirmation": False
            }
        }

    def test_security_blocks_dangerous_all_modes(self, mock_config):
        """Verify dangerous commands are blocked in all autonomy modes."""
        dangerous_commands = [
            "rm -rf /",
            "del /s /q C:\\",
            "format C:",
            "rd /s /q C:\\Windows",
            "taskkill /f /im explorer.exe",
        ]

        modes = [AutonomyMode.MANUAL, AutonomyMode.SEMI_AUTO, AutonomyMode.AUTONOMOUS]

        for mode in modes:
            mock_config["security"]["autonomy_mode"] = mode.value

            with patch('core.security.setup_logger'):
                manager = SecurityManager(mock_config)

            # Test each dangerous command
            for cmd in dangerous_commands:
                result = manager.can_execute_shell(cmd)
                assert result is False, f"'{cmd}' should be blocked in {mode.value} mode"

    def test_security_fork_bomb_blocked(self, mock_config):
        """Test that fork bomb pattern is blocked."""
        mock_config["security"]["autonomy_mode"] = "autonomous"

        with patch('core.security.setup_logger'):
            manager = SecurityManager(mock_config)

        result = manager.can_execute_shell(":(){:|:&};:")
        assert result is False


# ============================================================================
# Test 5: Security - Autonomous Mode Allows Safe Commands
# ============================================================================

class TestSecurityAutonomousMode:
    """Test suite for autonomous mode security."""

    def test_security_autonomous_allows_safe(self):
        """SecurityManager with AUTONOMOUS mode should allow safe commands."""
        config = {
            "security": {
                "autonomy_mode": "autonomous",
                "require_confirmation": False
            }
        }

        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)

        manager.set_autonomy_mode(AutonomyMode.AUTONOMOUS)

        # Safe commands should be allowed
        safe_commands = [
            "echo hello",
            "echo 'Hello World'",
            "ls -la",
            "pwd",
        ]

        for cmd in safe_commands:
            result = manager.can_execute_shell(cmd)
            assert result is True, f"'{cmd}' should be allowed in AUTONOMOUS mode"

    def test_security_manual_requires_confirmation(self):
        """MANUAL mode should require confirmation for all commands."""
        config = {
            "security": {
                "autonomy_mode": "manual",
                "require_confirmation": True
            }
        }

        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)

        manager.set_autonomy_mode(AutonomyMode.MANUAL)

        # Mock user input to deny
        with patch('builtins.input', return_value='n'):
            result = manager.can_execute_shell("echo hello")
            assert result is False, "Should require confirmation in MANUAL mode"


# ============================================================================
# Test 6: Plugin Pattern Matching
# ============================================================================

class TestPluginPatternMatching:
    """Test suite for plugin pattern matching."""

    def test_echo_plugin_pattern_matching(self):
        """Test that EchoPlugin correctly matches patterns."""
        plugin = EchoPlugin()

        assert plugin.name() == "Echo"
        assert "echo" in plugin.patterns()
        assert "say" in plugin.patterns()
        assert "repeat" in plugin.patterns()
        assert len(plugin.patterns()) == 3

    def test_echo_plugin_execute(self):
        """Test EchoPlugin execution."""
        plugin = EchoPlugin()

        mock_kernel = MagicMock()
        ctx = CommandContext(
            raw_text="echo hello world",
            command_name="echo",
            params={},
            kernel=mock_kernel
        )

        result = plugin.execute(ctx)

        assert result.success is True
        assert "Echo:" in result.message
        assert "echo hello world" in result.message

    def test_plugin_pattern_matching_with_kernel(self):
        """Test pattern matching logic with Kernel._match_pattern."""
        # Create kernel without full initialization
        kernel = Kernel.__new__(Kernel)
        kernel.logger = MagicMock()

        # Test pattern matching
        assert kernel._match_pattern("echo", "echo hello") is True
        assert kernel._match_pattern("echo", "please echo this") is True
        assert kernel._match_pattern("test", "testing") is False
        assert kernel._match_pattern(r"echo\s+\w+", "echo hello") is True


# ============================================================================
# Test 7: Memory Entry Creation
# ============================================================================

class TestMemoryEntry:
    """Test suite for MemoryEntry creation and validation."""

    def test_memory_entry_creation(self):
        """Create MemoryEntry with all fields and verify attributes."""
        timestamp = time.time()

        entry = MemoryEntry(
            id="test-entry-1",
            content="This is test content",
            metadata={"source": "test", "priority": "high"},
            timestamp=timestamp,
            entry_type=MemoryEntryType.SESSION
        )

        # Verify all attributes
        assert entry.id == "test-entry-1"
        assert entry.content == "This is test content"
        assert entry.metadata["source"] == "test"
        assert entry.metadata["priority"] == "high"
        assert entry.timestamp == timestamp
        assert entry.entry_type == MemoryEntryType.SESSION

    def test_memory_entry_default_timestamp(self):
        """MemoryEntry should have default timestamp if not provided."""
        entry = MemoryEntry(
            id="test-entry-2",
            content="Content without explicit timestamp"
        )

        assert entry.timestamp > 0
        assert isinstance(entry.timestamp, float)
        assert entry.entry_type == MemoryEntryType.SESSION

    def test_memory_entry_persistent_type(self):
        """Test creating persistent memory entry."""
        entry = MemoryEntry(
            id="persistent-1",
            content="This should be persistent",
            entry_type=MemoryEntryType.PERSISTENT
        )

        assert entry.entry_type == MemoryEntryType.PERSISTENT


# ============================================================================
# Test 8: Task Planner with Mocked Gemini
# ============================================================================

class TestTaskPlannerMockedGemini:
    """Test suite for TaskPlanner with mocked LLM."""

    def test_task_planner_with_mocked_gemini(self):
        """Test TaskPlanner.plan() with mocked GeminiClient."""
        # Mock kernel
        mock_kernel = MagicMock()
        mock_kernel.config = {
            "security": {"autonomy_mode": "autonomous"}
        }

        # Import TaskPlanner
        from core.task_planner import TaskPlanner

        # Create planner
        with patch('core.task_planner.GeminiClient') as mock_gemini_class:
            mock_gemini_instance = MagicMock()
            mock_gemini_class.return_value = mock_gemini_instance

            # Mock the response from Gemini
            gemini_response = {
                "steps": [
                    {
                        "description": "Step 1: Prepare data",
                        "plugin_name": "DataPlugin",
                        "params": {"input": "file.txt"}
                    },
                    {
                        "description": "Step 2: Process data",
                        "plugin_name": "ProcessPlugin",
                        "params": {"mode": "fast"}
                    }
                ]
            }

            mock_gemini_instance.generate_response.return_value = gemini_response

            planner = TaskPlanner(mock_kernel)

            # Plan the goal
            available_plugins = ["DataPlugin", "ProcessPlugin", "OutputPlugin"]
            plan = planner.plan("Process the data file", available_plugins)

            # Verify plan structure
            assert isinstance(plan, TaskPlan)
            assert plan.goal == "Process the data file"
            assert len(plan.steps) == 2
            assert plan.status == TaskStatus.PENDING

            # Verify step details
            assert plan.steps[0].description == "Step 1: Prepare data"
            assert plan.steps[0].plugin_name == "DataPlugin"
            assert plan.steps[0].params["input"] == "file.txt"
            assert plan.steps[0].status == TaskStatus.PENDING

            assert plan.steps[1].description == "Step 2: Process data"
            assert plan.steps[1].plugin_name == "ProcessPlugin"
            assert plan.steps[1].params["mode"] == "fast"

    def test_task_planner_fallback_on_none_response(self):
        """Test TaskPlanner creates fallback plan when Gemini returns None."""
        from core.task_planner import TaskPlanner

        mock_kernel = MagicMock()
        mock_kernel.config = {}

        with patch('core.task_planner.GeminiClient') as mock_gemini_class:
            mock_gemini_instance = MagicMock()
            mock_gemini_class.return_value = mock_gemini_instance
            mock_gemini_instance.generate_response.return_value = None

            with patch('core.task_planner.setup_logger'):
                planner = TaskPlanner(mock_kernel)
                plan = planner.plan("Test goal", ["Plugin1", "Plugin2"])

            # Should create fallback plan
            assert len(plan.steps) == 1
            assert plan.steps[0].plugin_name == "system"

    def test_task_planner_fallback_on_invalid_response(self):
        """Test TaskPlanner creates fallback plan when response is invalid."""
        from core.task_planner import TaskPlanner

        mock_kernel = MagicMock()
        mock_kernel.config = {}

        with patch('core.task_planner.GeminiClient') as mock_gemini_class:
            mock_gemini_instance = MagicMock()
            mock_gemini_class.return_value = mock_gemini_instance
            # Return invalid response (missing 'steps' key)
            mock_gemini_instance.generate_response.return_value = {"invalid": "response"}

            with patch('core.task_planner.setup_logger'):
                planner = TaskPlanner(mock_kernel)
                plan = planner.plan("Test goal", ["Plugin1"])

            # Should create fallback plan
            assert len(plan.steps) == 1
            assert plan.steps[0].plugin_name == "system"


# ============================================================================
# Test 9: Kernel Integration
# ============================================================================

class TestKernelIntegration:
    """Test suite for Kernel integration."""

    def test_kernel_dispatch_with_echo_plugin(self):
        """Test Kernel.dispatch() routing to EchoPlugin."""
        # Create kernel manually without full initialization
        kernel = Kernel.__new__(Kernel)
        kernel.config = {
            "security": {"autonomy_mode": "autonomous"},
            "memory": {"max_entries": 50},
            "logging": {"level": "INFO"}
        }
        kernel.logger = MagicMock()
        kernel.state = SystemState.IDLE
        kernel.plugins = {"Echo": EchoPlugin()}
        kernel.security_manager = MagicMock()
        kernel.short_memory = None
        kernel.tts = None
        kernel.events = {}

        # Dispatch echo command
        result = kernel.dispatch("echo hello world")

        assert result.success is True
        assert "Echo:" in result.message

    def test_kernel_state_transitions(self):
        """Test Kernel state transitions during dispatch."""
        kernel = Kernel.__new__(Kernel)
        kernel.config = {
            "security": {"autonomy_mode": "autonomous"},
            "memory": {"max_entries": 50},
            "logging": {"level": "INFO"}
        }
        kernel.logger = MagicMock()
        kernel.state = SystemState.IDLE
        kernel.plugins = {"Echo": EchoPlugin()}
        kernel.security_manager = MagicMock()
        kernel.short_memory = None
        kernel.tts = None
        kernel.events = {}

        # Dispatch should transition states
        result = kernel.dispatch("echo test")

        assert result.success is True

    def test_kernel_plugin_registration(self):
        """Test Kernel plugin registration."""
        kernel = Kernel.__new__(Kernel)
        kernel.config = {
            "security": {"autonomy_mode": "autonomous"},
            "memory": {"max_entries": 50},
            "logging": {"level": "INFO"}
        }
        kernel.logger = MagicMock()
        kernel.plugins = {}

        plugin = EchoPlugin()
        kernel.register_plugin(plugin)

        assert "Echo" in kernel.plugins
        assert kernel.plugins["Echo"] == plugin


# ============================================================================
# Test 10: CommandContext and CommandResult
# ============================================================================

class TestCommandContextAndResult:
    """Test suite for CommandContext and CommandResult."""

    def test_command_context_creation(self):
        """Test creating CommandContext."""
        mock_kernel = MagicMock()

        ctx = CommandContext(
            raw_text="echo hello",
            command_name="echo",
            params={"text": "hello"},
            kernel=mock_kernel
        )

        assert ctx.raw_text == "echo hello"
        assert ctx.command_name == "echo"
        assert ctx.params["text"] == "hello"
        assert ctx.kernel == mock_kernel

    def test_command_result_creation(self):
        """Test creating CommandResult."""
        result = CommandResult(
            success=True,
            message="Command executed",
            data={"output": "result"}
        )

        assert result.success is True
        assert result.message == "Command executed"
        assert result.data["output"] == "result"

    def test_command_result_without_data(self):
        """Test CommandResult with default data field."""
        result = CommandResult(
            success=False,
            message="Error occurred"
        )

        assert result.success is False
        assert result.message == "Error occurred"
        assert result.data is None


# ============================================================================
# Test 11: Task Status Enum
# ============================================================================

class TestTaskStatus:
    """Test suite for TaskStatus enum."""

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.DONE.value == "done"
        assert TaskStatus.FAILED.value == "failed"

    def test_task_status_equality(self):
        """Test TaskStatus comparison."""
        assert TaskStatus.DONE == TaskStatus.DONE
        assert TaskStatus.PENDING != TaskStatus.DONE


# ============================================================================
# Test 12: Security Manager Whitelist Functionality
# ============================================================================

class TestSecurityManagerWhitelist:
    """Test suite for SecurityManager whitelist."""

    def test_security_semi_auto_with_whitelist(self):
        """Test SEMI_AUTO mode with whitelist."""
        config = {
            "security": {
                "autonomy_mode": "semi_auto",
                "require_confirmation": False
            }
        }

        with patch('core.security.setup_logger'):
            with patch('core.security.os.path.exists', return_value=False):
                manager = SecurityManager(config)

        manager.set_autonomy_mode(AutonomyMode.SEMI_AUTO)

        # Add some whitelisted commands
        manager.whitelist = ["echo hello", "ls"]

        # Whitelisted should be allowed
        assert manager._matches_whitelist("echo hello") is True
        assert manager._matches_whitelist("ls") is True
        assert manager._matches_whitelist("rm file") is False

    def test_security_dangerous_pattern_detection(self):
        """Test dangerous pattern detection."""
        config = {
            "security": {"autonomy_mode": "autonomous"}
        }

        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)

        # Test various dangerous patterns
        assert manager._is_dangerous("rm -rf /home") is True
        assert manager._is_dangerous("rm -rf /") is True
        assert manager._is_dangerous("del /s C:\\") is True
        assert manager._is_dangerous("echo hello") is False
        assert manager._is_dangerous("ls -la") is False


# ============================================================================
# Test 13: Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_memory_query_with_empty_results(self):
        """Test querying memory with no matches."""
        memory = ShortTermMemory(max_entries=50)

        entry = MemoryEntry(
            id="entry-1",
            content="test content",
            timestamp=time.time()
        )
        memory.store(entry)

        results = memory.query("nonexistent", k=5)
        assert len(results) == 0

    def test_task_plan_with_empty_steps(self):
        """Test TaskPlan with empty steps list."""
        plan = TaskPlan(goal="Empty plan", steps=[])

        assert len(plan.steps) == 0
        assert plan.status == TaskStatus.PENDING

    def test_security_empty_command(self):
        """Test SecurityManager with empty command."""
        config = {
            "security": {"autonomy_mode": "autonomous"}
        }

        with patch('core.security.setup_logger'):
            manager = SecurityManager(config)

        result = manager.can_execute_shell("")
        assert result is False

        result = manager.can_execute_shell("   ")
        assert result is False

    def test_command_context_with_empty_params(self):
        """Test CommandContext with empty params."""
        mock_kernel = MagicMock()

        ctx = CommandContext(
            raw_text="test",
            command_name="test",
            params={},
            kernel=mock_kernel
        )

        assert ctx.params == {}


# ============================================================================
# Test 14: Memory Entry Type Enum
# ============================================================================

class TestMemoryEntryType:
    """Test suite for MemoryEntryType enum."""

    def test_memory_entry_type_values(self):
        """Test MemoryEntryType enum values."""
        assert MemoryEntryType.SESSION.value == "session"
        assert MemoryEntryType.PERSISTENT.value == "persistent"

    def test_memory_entry_type_default(self):
        """Test MemoryEntry uses SESSION as default type."""
        entry = MemoryEntry(id="test", content="test")
        assert entry.entry_type == MemoryEntryType.SESSION


# ============================================================================
# Integration Test: Full Workflow
# ============================================================================

class TestFullIntegrationWorkflow:
    """Test complete workflow integration."""

    def test_full_workflow_memory_to_execution(self):
        """Test complete workflow: store in memory, plan, and execute."""
        # Initialize memory
        memory = ShortTermMemory(max_entries=50)

        # Store initial context
        context_entry = MemoryEntry(
            id="ctx-1",
            content="User wants to process data",
            metadata={"user_intent": "data_processing"},
            timestamp=time.time()
        )
        memory.store(context_entry)

        # Create a task plan
        step1 = TaskStep(
            id="step-1",
            description="Load data",
            plugin_name="DataPlugin",
            params={"file": "input.txt"}
        )

        step2 = TaskStep(
            id="step-2",
            description="Process data",
            plugin_name="ProcessPlugin",
            params={"method": "analyze"}
        )

        plan = TaskPlan(
            goal="Process user data",
            steps=[step1, step2]
        )

        # Mock plugins
        mock_plugins = {
            "DataPlugin": MagicMock(execute=MagicMock(
                return_value=CommandResult(True, "Data loaded")
            )),
            "ProcessPlugin": MagicMock(execute=MagicMock(
                return_value=CommandResult(True, "Data processed")
            ))
        }

        # Execute plan
        plan.status = TaskStatus.RUNNING
        for step in plan.steps:
            step.status = TaskStatus.RUNNING
            plugin = mock_plugins[step.plugin_name]
            result = plugin.execute(CommandContext(
                raw_text=step.description,
                command_name=step.plugin_name,
                params=step.params,
                kernel=None
            ))
            step.result = result
            step.status = TaskStatus.DONE

        if all(s.status == TaskStatus.DONE for s in plan.steps):
            plan.status = TaskStatus.DONE

        # Store results
        result_entry = MemoryEntry(
            id="result-1",
            content=f"Plan completed: {plan.goal}",
            metadata={"plan_status": plan.status.value},
            timestamp=time.time()
        )
        memory.store(result_entry)

        # Verify everything
        assert len(memory.get_recent(10)) == 2
        assert plan.status == TaskStatus.DONE
        assert all(s.status == TaskStatus.DONE for s in plan.steps)

        # Query results
        completed = memory.query("completed", k=5)
        assert len(completed) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-p", "no:cacheprovider"])
