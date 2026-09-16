"""
Template Service
Handles dynamic content rendering for emails and other text-based outputs
Supports variable substitution from workflow execution results
"""

import re
import json
from typing import Any, Dict


class TemplateService:
    """Service for rendering templates with dynamic content"""

    @staticmethod
    def render(template: str, context: Dict[str, Any]) -> str:
        """
        Render a template with variable substitution

        Supports multiple variable formats:
        - {{variable}} - Simple variable
        - {{node.result}} - Nested property access
        - {{input_data.text}} - Deep nested access
        - ${{variable}} - Alternative syntax

        Args:
            template: Template string with placeholders
            context: Dictionary of available variables

        Returns:
            Rendered string with variables replaced

        Examples:
            >>> render("Hello {{name}}!", {"name": "World"})
            "Hello World!"

            >>> render("Result: {{llm.response}}", {"llm": {"response": "Success"}})
            "Result: Success"
        """
        if not template:
            return template

        # Pattern to match {{variable}} or {{object.property}}
        pattern = r'\{\{([^}]+)\}\}'

        def replacer(match):
            variable_path = match.group(1).strip()
            value = TemplateService._get_nested_value(context, variable_path)

            # Convert value to string representation
            if value is None:
                return f"{{{{⚠️ {variable_path} not found}}}}"
            elif isinstance(value, (dict, list)):
                return json.dumps(value, indent=2)
            else:
                return str(value)

        # Replace all variables in the template
        result = re.sub(pattern, replacer, template)
        return result

    @staticmethod
    def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
        """
        Get nested value from dictionary using dot notation

        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., "user.name" or "results.0.value")

        Returns:
            Value at the path, or None if not found
        """
        keys = path.split('.')
        current = data

        for key in keys:
            if current is None:
                return None

            # Handle list indexing
            if isinstance(current, list):
                try:
                    index = int(key)
                    current = current[index] if 0 <= index < len(current) else None
                except (ValueError, IndexError):
                    return None
            # Handle dictionary access
            elif isinstance(current, dict):
                current = current.get(key)
            else:
                # Can't navigate further
                return None

        return current

    @staticmethod
    def get_available_variables(execution_results: Dict[str, Any]) -> Dict[str, str]:
        """
        Get a dictionary of available variables from workflow execution results

        Args:
            execution_results: Results from workflow execution

        Returns:
            Dictionary mapping variable names to their descriptions
        """
        variables = {}

        for node_id, result in execution_results.items():
            # Add top-level node result
            variables[node_id] = f"Full result from node '{node_id}'"

            # Add commonly used nested properties
            if isinstance(result, dict):
                for key in result.keys():
                    var_name = f"{node_id}.{key}"
                    variables[var_name] = f"Property '{key}' from node '{node_id}'"

        return variables

    @staticmethod
    def create_email_templates() -> Dict[str, Dict[str, str]]:
        """
        Create pre-defined email templates for common use cases

        Returns:
            Dictionary of template configurations
        """
        templates = {
            "workflow_complete": {
                "name": "Workflow Completion",
                "subject": "Workflow Completed: {{workflow_name}}",
                "body": """
Hello,

Your workflow "{{workflow_name}}" has completed successfully.

Execution Time: {{execution_time}}
Status: {{status}}

Results:
{{results}}

Best regards,
Agentic Workflow System
""".strip()
            },

            "llm_summary": {
                "name": "LLM Summary Report",
                "subject": "AI Analysis Complete",
                "body": """
AI Analysis Results:

Input: {{input_data}}

AI Response:
{{llm_response}}

Generated at: {{timestamp}}
Model: {{model_name}}
""".strip()
            },

            "data_report": {
                "name": "Data Processing Report",
                "subject": "Data Processing Complete - {{record_count}} records",
                "body": """
Data Processing Summary:

Records Processed: {{record_count}}
Success Rate: {{success_rate}}%

Sample Results:
{{sample_data}}

Full results available in the attached workflow execution.
""".strip()
            },

            "error_notification": {
                "name": "Error Notification",
                "subject": "⚠️ Workflow Error: {{workflow_name}}",
                "body": """
Warning: Your workflow encountered an error.

Workflow: {{workflow_name}}
Error: {{error_message}}
Node: {{failed_node}}

Please review the workflow configuration and try again.

Error Details:
{{error_details}}
""".strip()
            },

            "approval_request": {
                "name": "Approval Request",
                "subject": "Action Required: Approve {{item_name}}",
                "body": """
Hello,

The following item requires your approval:

Item: {{item_name}}
Description: {{item_description}}
Requested by: {{requester}}
Date: {{request_date}}

Details:
{{item_details}}

Please review and take action.
""".strip()
            }
        }

        return templates


# Global template service instance
template_service = TemplateService()
