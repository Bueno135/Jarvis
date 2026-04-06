import unittest
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock the google.genai module before importing anything that depends on it
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()

from core.task_planner import TaskPlanner
from core.interfaces import TaskPlan, TaskStep, TaskStatus


class TestTaskPlanner(unittest.TestCase):
    """
    Unit tests for the TaskPlanner implementation.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.mock_kernel = Mock()
        self.mock_kernel.config = {
            "ai": {"api_key_env": "GEMINI_API_KEY", "model": "gemini-2.0-flash"},
            "logging": {"level": "DEBUG"},
        }

    @patch("core.task_planner.GeminiClient")
    def test_plan_success(self, mock_gemini_class):
        """
        Test successful plan generation with valid JSON from LLM.
        """
        # Setup mock Gemini client
        mock_gemini = Mock()
        mock_gemini_class.return_value = mock_gemini

        # Mock the LLM response
        mock_response = {
            "steps": [
                {
                    "description": "Open email application",
                    "plugin_name": "email",
                    "params": {"app": "gmail"},
                },
                {
                    "description": "Check recent emails",
                    "plugin_name": "email",
                    "params": {"filter": "recent"},
                },
                {
                    "description": "Compose a reply",
                    "plugin_name": "email",
                    "params": {"action": "compose"},
                },
            ]
        }
        mock_gemini.generate_response.return_value = mock_response

        # Create planner and generate plan
        planner = TaskPlanner(self.mock_kernel)
        goal = "Check emails and reply to important messages"
        available_plugins = ["email", "calendar", "notes"]

        plan = planner.plan(goal, available_plugins)

        # Assertions
        self.assertIsInstance(plan, TaskPlan)
        self.assertEqual(plan.goal, goal)
        self.assertEqual(len(plan.steps), 3)
        self.assertEqual(plan.current_step_index, 0)
        self.assertEqual(plan.status, TaskStatus.PENDING)

        # Verify step details
        self.assertEqual(plan.steps[0].id, "step-1")
        self.assertEqual(plan.steps[0].description, "Open email application")
        self.assertEqual(plan.steps[0].plugin_name, "email")
        self.assertEqual(plan.steps[0].params, {"app": "gmail"})
        self.assertEqual(plan.steps[0].status, TaskStatus.PENDING)

        self.assertEqual(plan.steps[1].id, "step-2")
        self.assertEqual(plan.steps[2].id, "step-3")

        # Verify Gemini was called with appropriate prompt
        mock_gemini.generate_response.assert_called_once()
        call_args = mock_gemini.generate_response.call_args[0][0]
        self.assertIn(goal, call_args)
        self.assertIn("email", call_args)
        self.assertIn("calendar", call_args)

    @patch("core.task_planner.GeminiClient")
    def test_plan_invalid_json(self, mock_gemini_class):
        """
        Test fallback behavior when LLM returns invalid/unparseable response.
        """
        # Setup mock Gemini client that returns invalid structure
        mock_gemini = Mock()
        mock_gemini_class.return_value = mock_gemini

        # Mock invalid response (missing 'steps' key)
        mock_response = {"invalid": "structure"}
        mock_gemini.generate_response.return_value = mock_response

        # Create planner and generate plan
        planner = TaskPlanner(self.mock_kernel)
        goal = "Do something complex"
        available_plugins = ["plugin1", "plugin2"]

        plan = planner.plan(goal, available_plugins)

        # Should return a fallback plan
        self.assertIsInstance(plan, TaskPlan)
        self.assertEqual(plan.goal, goal)
        self.assertEqual(len(plan.steps), 1)

        # Verify fallback step
        fallback_step = plan.steps[0]
        self.assertEqual(fallback_step.id, "step-1")
        self.assertEqual(fallback_step.plugin_name, "system")
        self.assertIn(goal, fallback_step.description)
        self.assertEqual(fallback_step.status, TaskStatus.PENDING)

    @patch("core.task_planner.GeminiClient")
    def test_plan_empty_plugins(self, mock_gemini_class):
        """
        Test plan generation with empty available plugins list.
        """
        # Setup mock Gemini client
        mock_gemini = Mock()
        mock_gemini_class.return_value = mock_gemini

        # Mock response with no plugin-specific steps
        mock_response = {
            "steps": [
                {
                    "description": "Execute system command",
                    "plugin_name": "system",
                    "params": {"command": "echo hello"},
                }
            ]
        }
        mock_gemini.generate_response.return_value = mock_response

        # Create planner with empty plugins list
        planner = TaskPlanner(self.mock_kernel)
        goal = "Say hello"
        available_plugins = []

        plan = planner.plan(goal, available_plugins)

        # Assertions
        self.assertIsInstance(plan, TaskPlan)
        self.assertEqual(plan.goal, goal)
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].plugin_name, "system")

        # Verify that the prompt mentions no plugins
        mock_gemini.generate_response.assert_called_once()
        call_args = mock_gemini.generate_response.call_args[0][0]
        self.assertIn("none", call_args)

    @patch("core.task_planner.GeminiClient")
    def test_plan_gemini_returns_none(self, mock_gemini_class):
        """
        Test fallback behavior when Gemini API returns None.
        """
        # Setup mock Gemini client that returns None
        mock_gemini = Mock()
        mock_gemini_class.return_value = mock_gemini
        mock_gemini.generate_response.return_value = None

        # Create planner and generate plan
        planner = TaskPlanner(self.mock_kernel)
        goal = "Test goal"
        available_plugins = ["test"]

        plan = planner.plan(goal, available_plugins)

        # Should return a fallback plan
        self.assertIsInstance(plan, TaskPlan)
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].plugin_name, "system")

    @patch("core.task_planner.GeminiClient")
    def test_plan_response_with_missing_fields(self, mock_gemini_class):
        """
        Test plan generation when response has missing optional fields.
        """
        # Setup mock Gemini client
        mock_gemini = Mock()
        mock_gemini_class.return_value = mock_gemini

        # Mock response with minimal fields
        mock_response = {
            "steps": [
                {
                    "description": "Step with minimal fields",
                    # Missing plugin_name, params
                }
            ]
        }
        mock_gemini.generate_response.return_value = mock_response

        # Create planner and generate plan
        planner = TaskPlanner(self.mock_kernel)
        goal = "Test goal"
        available_plugins = ["test"]

        plan = planner.plan(goal, available_plugins)

        # Should handle missing fields gracefully
        self.assertIsInstance(plan, TaskPlan)
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].plugin_name, "system")  # Default
        self.assertEqual(plan.steps[0].params, {})  # Default

    @patch("core.task_planner.GeminiClient")
    def test_plan_response_steps_not_list(self, mock_gemini_class):
        """
        Test fallback behavior when 'steps' is not a list.
        """
        # Setup mock Gemini client
        mock_gemini = Mock()
        mock_gemini_class.return_value = mock_gemini

        # Mock response with steps as dict instead of list
        mock_response = {
            "steps": {"invalid": "format"}  # Should be a list
        }
        mock_gemini.generate_response.return_value = mock_response

        # Create planner and generate plan
        planner = TaskPlanner(self.mock_kernel)
        goal = "Test goal"
        available_plugins = []

        plan = planner.plan(goal, available_plugins)

        # Should return fallback plan
        self.assertIsInstance(plan, TaskPlan)
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].plugin_name, "system")

    @patch("core.task_planner.GeminiClient")
    def test_prompt_includes_all_plugins(self, mock_gemini_class):
        """
        Test that the generated prompt includes all available plugins.
        """
        # Setup mock Gemini client
        mock_gemini = Mock()
        mock_gemini_class.return_value = mock_gemini
        mock_gemini.generate_response.return_value = {"steps": []}

        # Create planner and generate plan
        planner = TaskPlanner(self.mock_kernel)
        goal = "Test goal"
        available_plugins = ["plugin_a", "plugin_b", "plugin_c"]

        planner.plan(goal, available_plugins)

        # Verify all plugins are in the prompt
        call_args = mock_gemini.generate_response.call_args[0][0]
        for plugin in available_plugins:
            self.assertIn(plugin, call_args)

    @patch("core.task_planner.GeminiClient")
    def test_step_ids_are_sequential(self, mock_gemini_class):
        """
        Test that step IDs are generated sequentially (step-1, step-2, etc.).
        """
        # Setup mock Gemini client
        mock_gemini = Mock()
        mock_gemini_class.return_value = mock_gemini

        mock_response = {
            "steps": [
                {"description": "Step 1", "plugin_name": "p1", "params": {}},
                {"description": "Step 2", "plugin_name": "p2", "params": {}},
                {"description": "Step 3", "plugin_name": "p3", "params": {}},
                {"description": "Step 4", "plugin_name": "p4", "params": {}},
            ]
        }
        mock_gemini.generate_response.return_value = mock_response

        planner = TaskPlanner(self.mock_kernel)
        plan = planner.plan("Test", [])

        # Verify sequential IDs
        expected_ids = ["step-1", "step-2", "step-3", "step-4"]
        actual_ids = [step.id for step in plan.steps]
        self.assertEqual(actual_ids, expected_ids)


if __name__ == "__main__":
    unittest.main()
