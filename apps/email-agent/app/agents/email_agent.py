"""Email agent implementation."""

from typing import Dict, Any
from core.agents import ToolExecutionAgent
from core.logger import logger

from ..tools.email_tools import EmailTools


class EmailAgent(ToolExecutionAgent):
    """Email processing agent."""

    def __init__(self, *args, **kwargs):
        """Initialize email agent."""
        super().__init__(*args, **kwargs)
        # Register email-specific tools
        email_tools = EmailTools()
        email_tools.register_all(self.tools)

    def get_system_prompt(self) -> str:
        """Get system prompt for email agent."""
        return """You are an email assistant agent. Your role is to:
1. Analyze incoming emails
2. Categorize emails (urgent, important, spam, general)
3. Determine priority levels
4. Generate appropriate responses
5. Suggest actions (reply, forward, archive, delete)

Be concise, professional, and helpful."""

    def act(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process email input.

        Args:
            input_data: Input with 'email', 'subject', 'from' keys

        Returns:
            Dictionary with response, category, priority, suggested_action
        """
        email = input_data.get("email", "")
        subject = input_data.get("subject", "")
        from_email = input_data.get("from", "")

        query = f"""
        Email from: {from_email}
        Subject: {subject}
        Content: {email}

        Please analyze this email and:
        1. Categorize it
        2. Determine priority
        3. Suggest an action
        4. Generate a response if needed
        """

        input_data["query"] = query
        result = super().act(input_data)

        # Enhance result with email-specific fields
        response_text = result.get("response", "")
        result["category"] = self._extract_category(response_text)
        result["priority"] = self._extract_priority(response_text)
        result["suggested_action"] = self._extract_action(response_text)

        return result

    def _extract_category(self, text: str) -> str:
        """Extract category from response text."""
        text_lower = text.lower()
        if "urgent" in text_lower or "critical" in text_lower:
            return "urgent"
        elif "important" in text_lower:
            return "important"
        elif "spam" in text_lower:
            return "spam"
        return "general"

    def _extract_priority(self, text: str) -> str:
        """Extract priority from response text."""
        text_lower = text.lower()
        if "high" in text_lower or "urgent" in text_lower:
            return "high"
        elif "low" in text_lower:
            return "low"
        return "normal"

    def _extract_action(self, text: str) -> str:
        """Extract suggested action from response text."""
        text_lower = text.lower()
        if "reply" in text_lower:
            return "reply"
        elif "forward" in text_lower:
            return "forward"
        elif "archive" in text_lower:
            return "archive"
        elif "delete" in text_lower:
            return "delete"
        return "read"

