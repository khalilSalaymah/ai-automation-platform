"""Email-specific tools."""

from core.tools import Tool, ToolRegistry
from core.logger import logger


class EmailTools:
    """Email processing tools."""

    def __init__(self):
        """Initialize email tools."""
        pass

    def register_all(self, registry: ToolRegistry):
        """Register all email tools."""
        registry.register_function(
            "extract_email_info",
            "Extract key information from an email",
            self.extract_email_info,
            {
                "type": "object",
                "properties": {
                    "email_text": {"type": "string", "description": "The email content"},
                },
                "required": ["email_text"],
            },
        )

        registry.register_function(
            "check_spam",
            "Check if an email is spam",
            self.check_spam,
            {
                "type": "object",
                "properties": {
                    "email_text": {"type": "string"},
                    "from_email": {"type": "string"},
                },
                "required": ["email_text", "from_email"],
            },
        )

    @staticmethod
    def extract_email_info(email_text: str) -> dict:
        """
        Extract key information from email.

        Args:
            email_text: Email content

        Returns:
            Dictionary with extracted info
        """
        # Simple extraction - can be enhanced with NLP
        return {
            "has_question": "?" in email_text,
            "has_urgent_keywords": any(
                word in email_text.lower()
                for word in ["urgent", "asap", "immediately", "critical"]
            ),
            "word_count": len(email_text.split()),
        }

    @staticmethod
    def check_spam(email_text: str, from_email: str) -> dict:
        """
        Check if email is spam.

        Args:
            email_text: Email content
            from_email: Sender email address

        Returns:
            Dictionary with spam check results
        """
        # Simple spam detection - can be enhanced
        spam_keywords = ["free", "winner", "click here", "limited time"]
        is_spam = any(keyword in email_text.lower() for keyword in spam_keywords)

        return {
            "is_spam": is_spam,
            "confidence": 0.8 if is_spam else 0.2,
            "reason": "Contains spam keywords" if is_spam else "Appears legitimate",
        }

