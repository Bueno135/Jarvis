import json
import logging
from typing import List, Any, Optional
from core.interfaces import TaskPlannerBase, TaskPlan, TaskStep, TaskStatus
from core.ai.gemini_client import GeminiClient
from core.logger import setup_logger


class TaskPlanner(TaskPlannerBase):
    """
    Implementation of TaskPlannerBase that uses Gemini API to decompose goals into task steps.
    """

    def __init__(self, kernel: Any):
        """
        Initialize the TaskPlanner with a kernel instance.

        Args:
            kernel: The Kernel instance providing access to services and configuration.
        """
        self.kernel = kernel
        self.logger = setup_logger("Jarvis.TaskPlanner", kernel.config if hasattr(kernel, 'config') else {})

        # Initialize Gemini client
        try:
            gemini_config = kernel.config if hasattr(kernel, 'config') else {}
            self.gemini_client = GeminiClient(gemini_config)
            self.logger.info("TaskPlanner initialized with Gemini client")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {e}")
            self.gemini_client = None

    def plan(self, goal: str, available_plugins: List[str]) -> TaskPlan:
        """
        Generates a task plan to achieve the given goal by decomposing it into steps.

        Uses the Gemini API to analyze the goal and available plugins, then creates
        a structured task plan with individual steps.

        Args:
            goal: The overall goal to achieve.
            available_plugins: List of plugin names available for use.

        Returns:
            TaskPlan: A plan with steps to achieve the goal.
        """
        self.logger.debug(f"Planning goal: '{goal}' with plugins: {available_plugins}")

        # Build the prompt for the LLM
        prompt = self._build_planning_prompt(goal, available_plugins)

        # Call Gemini API
        if self.gemini_client is None:
            self.logger.error("Gemini client not available, returning fallback plan")
            return self._create_fallback_plan(goal)

        response = self.gemini_client.generate_response(prompt)

        # Handle response and parse JSON
        if response is None:
            self.logger.warning("Gemini API returned None, using fallback plan")
            return self._create_fallback_plan(goal)

        # Parse the response
        try:
            plan = self._parse_plan_response(response, goal)
            self.logger.info(f"Successfully created plan with {len(plan.steps)} steps")
            return plan
        except (KeyError, TypeError, ValueError) as e:
            self.logger.error(f"Failed to parse plan response: {e}. Response: {response}")
            return self._create_fallback_plan(goal)

    def _build_planning_prompt(self, goal: str, available_plugins: List[str]) -> str:
        """
        Builds a detailed prompt for the LLM to decompose the goal into steps.

        Args:
            goal: The goal to decompose.
            available_plugins: List of available plugin names.

        Returns:
            str: The formatted prompt.
        """
        plugins_list = ", ".join(available_plugins) if available_plugins else "none"

        prompt = f"""You are a task planning assistant. Your job is to decompose a user goal into concrete, executable steps.

Goal: {goal}

Available Plugins: {plugins_list}

Analyze the goal and create a step-by-step plan. Each step must specify:
1. A clear description of what needs to be done
2. Which plugin to use (must be from the available plugins list, or "system" if no plugin is needed)
3. Parameters required for that step (as a JSON object)

Return your response as a valid JSON object with this structure:
{{
    "steps": [
        {{
            "description": "Description of step 1",
            "plugin_name": "plugin_name_or_system",
            "params": {{"param1": "value1", "param2": "value2"}}
        }},
        {{
            "description": "Description of step 2",
            "plugin_name": "another_plugin",
            "params": {{"key": "value"}}
        }}
    ]
}}

Important:
- Create as many steps as needed to fully achieve the goal
- If no plugins match the goal, use "system" as the plugin_name
- Ensure all parameters are strings or simple JSON types
- Return ONLY valid JSON, no markdown formatting or extra text
"""
        return prompt

    def _parse_plan_response(self, response: dict, goal: str) -> TaskPlan:
        """
        Parses the LLM response into a TaskPlan object.

        Args:
            response: The parsed JSON response from the LLM.
            goal: The original goal.

        Returns:
            TaskPlan: The constructed task plan.

        Raises:
            KeyError, TypeError, ValueError: If the response structure is invalid.
        """
        if "steps" not in response:
            raise KeyError("Response missing required 'steps' key")

        steps_data = response.get("steps", [])

        if not isinstance(steps_data, list):
            raise TypeError(f"Expected 'steps' to be a list, got {type(steps_data)}")

        if not steps_data:
            raise ValueError("Response 'steps' list is empty")

        steps = []
        for idx, step_data in enumerate(steps_data, start=1):
            step = TaskStep(
                id=f"step-{idx}",
                description=step_data.get("description", ""),
                plugin_name=step_data.get("plugin_name", "system"),
                params=step_data.get("params", {}),
                status=TaskStatus.PENDING,
                result=None
            )
            steps.append(step)

        plan = TaskPlan(
            goal=goal,
            steps=steps,
            current_step_index=0,
            status=TaskStatus.PENDING
        )

        return plan

    def _create_fallback_plan(self, goal: str) -> TaskPlan:
        """
        Creates a simple fallback plan when LLM planning fails.

        Args:
            goal: The goal to achieve.

        Returns:
            TaskPlan: A single-step fallback plan.
        """
        self.logger.warning(f"Creating fallback plan for goal: {goal}")

        fallback_step = TaskStep(
            id="step-1",
            description=f"Execute: {goal}",
            plugin_name="system",
            params={"goal": goal},
            status=TaskStatus.PENDING,
            result=None
        )

        plan = TaskPlan(
            goal=goal,
            steps=[fallback_step],
            current_step_index=0,
            status=TaskStatus.PENDING
        )

        return plan
