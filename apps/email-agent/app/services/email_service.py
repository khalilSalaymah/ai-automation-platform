"""Email service business logic."""

from typing import List
from core.logger import logger
from core import LLM, RedisSessionMemory
from core.config import get_settings

from ..agents.email_agent import EmailAgent
from ..models.email_models import EmailRequest, EmailResponse, EmailHistory
from ..config import settings

settings_core = get_settings()


class EmailService:
    """Email processing service."""

    def __init__(self):
        """Initialize email service."""
        self.llm = LLM(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
        self.memory = RedisSessionMemory(url=settings.redis_url)
        self.agent = EmailAgent(
            name="email-agent",
            llm=self.llm,
            memory=self.memory,
        )

    async def process_email(self, request: EmailRequest) -> EmailResponse:
        """
        Process an incoming email.

        Args:
            request: Email request data

        Returns:
            Email response with processing results
        """
        try:
            input_data = {
                "email": request.email,
                "subject": request.subject,
                "from": request.from_email,
                "session_id": request.session_id or "default",
            }

            result = self.agent.act(input_data)

            return EmailResponse(
                response=result.get("response", ""),
                category=result.get("category", "general"),
                priority=result.get("priority", "normal"),
                suggested_action=result.get("suggested_action", ""),
            )
        except Exception as e:
            logger.error(f"Error in process_email: {e}")
            raise

    async def generate_response(self, request: EmailRequest) -> EmailResponse:
        """
        Generate an email response.

        Args:
            request: Email request data

        Returns:
            Email response with generated reply
        """
        try:
            input_data = {
                "email": request.email,
                "subject": request.subject,
                "from": request.from_email,
                "action": "generate_response",
                "session_id": request.session_id or "default",
            }

            result = self.agent.act(input_data)

            return EmailResponse(
                response=result.get("response", ""),
                category=result.get("category", "general"),
                priority=result.get("priority", "normal"),
                suggested_action="reply",
            )
        except Exception as e:
            logger.error(f"Error in generate_response: {e}")
            raise

    async def get_history(self, limit: int = 10, offset: int = 0) -> List[EmailHistory]:
        """
        Get email processing history.

        Args:
            limit: Number of records to return
            offset: Offset for pagination

        Returns:
            List of email history records
        """
        # This would typically query a database
        # For now, return empty list
        return []


# Scheduled task functions (must be synchronous for RQ)
def process_pending_emails_task(batch_size: int = 10) -> dict:
    """
    Scheduled task to process pending emails.
    
    Args:
        batch_size: Number of emails to process in this batch
        
    Returns:
        Result dictionary
    """
    from core.logger import logger
    from core.event_bus import EventBus
    
    logger.info(f"Processing {batch_size} pending emails")
    # TODO: Implement actual email processing logic
    # This is a placeholder that shows the pattern
    
    # Example: Publish event when done
    event_bus = EventBus()
    event_bus.publish(
        event_type="email.batch_processed",
        source_agent="email-agent",
        payload={"batch_size": batch_size, "processed": 0}
    )
    
    return {"status": "success", "processed": 0, "batch_size": batch_size}


def cleanup_history_task(days_to_keep: int = 30) -> dict:
    """
    Scheduled task to clean up old email history.
    
    Args:
        days_to_keep: Number of days of history to keep
        
    Returns:
        Result dictionary
    """
    from core.logger import logger
    from datetime import datetime, timedelta
    
    logger.info(f"Cleaning up email history older than {days_to_keep} days")
    # TODO: Implement actual cleanup logic
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    return {"status": "success", "cutoff_date": cutoff_date.isoformat()}


def send_digest_task() -> dict:
    """
    Scheduled task to send daily email digest.
    
    Returns:
        Result dictionary
    """
    from core.logger import logger
    from core.event_bus import EventBus
    from datetime import datetime
    
    logger.info("Sending daily email digest")
    # TODO: Implement actual digest sending logic
    
    event_bus = EventBus()
    event_bus.publish(
        event_type="email.digest_sent",
        source_agent="email-agent",
        payload={"date": datetime.utcnow().isoformat()}
    )
    
    return {"status": "success", "digest_sent": True}