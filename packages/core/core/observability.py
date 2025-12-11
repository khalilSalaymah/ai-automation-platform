"""Observability utilities: Slack alerts and error tracking."""

import httpx
from typing import Optional, Dict, Any
from .logger import logger, get_trace_id, get_span_id
from .config import get_settings

settings = get_settings()


async def send_slack_alert(
    message: str,
    level: str = "error",
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Send error alert to Slack via webhook.
    
    Args:
        message: Error message
        level: Log level (error, warning, etc.)
        trace_id: Trace ID for correlation
        span_id: Span ID for correlation
        metadata: Additional metadata
    """
    if not settings.enable_slack_alerts or not settings.slack_webhook_url:
        return
    
    try:
        # Get trace context if not provided
        if not trace_id:
            trace_id = get_trace_id()
        if not span_id:
            span_id = get_span_id()
        
        # Build Slack message
        color = {
            "error": "#FF0000",
            "warning": "#FFA500",
            "critical": "#8B0000",
        }.get(level.lower(), "#808080")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {level.upper()} Alert",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Message:*\n{message}",
                },
            },
        ]
        
        # Add trace context
        fields = []
        if trace_id:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Trace ID:*\n`{trace_id}`",
            })
        if span_id:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Span ID:*\n`{span_id}`",
            })
        
        if fields:
            blocks.append({
                "type": "section",
                "fields": fields,
            })
        
        # Add metadata if provided
        if metadata:
            metadata_text = "\n".join([f"• *{k}:* {v}" for k, v in metadata.items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Metadata:*\n{metadata_text}",
                },
            })
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "blocks": blocks,
                }
            ],
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                settings.slack_webhook_url,
                json=payload,
            )
            response.raise_for_status()
            
    except Exception as e:
        # Don't fail if Slack webhook fails, just log it
        logger.warning(f"Failed to send Slack alert: {e}")


def log_error_with_alert(
    message: str,
    error: Optional[Exception] = None,
    metadata: Optional[Dict[str, Any]] = None,
    send_alert: bool = True,
):
    """
    Log error and optionally send Slack alert.
    
    Args:
        message: Error message
        error: Exception object
        metadata: Additional metadata
        send_alert: Whether to send Slack alert
    """
    trace_id = get_trace_id()
    span_id = get_span_id()
    
    log_metadata = metadata or {}
    log_metadata.update({
        "trace_id": trace_id,
        "span_id": span_id,
    })
    
    if error:
        logger.exception(message, **log_metadata)
    else:
        logger.error(message, **log_metadata)
    
    if send_alert:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a task
                asyncio.create_task(
                    send_slack_alert(
                        message=message,
                        level="error",
                        trace_id=trace_id,
                        span_id=span_id,
                        metadata=metadata,
                    )
                )
            else:
                # If no loop is running, run it
                loop.run_until_complete(
                    send_slack_alert(
                        message=message,
                        level="error",
                        trace_id=trace_id,
                        span_id=span_id,
                        metadata=metadata,
                    )
                )
        except RuntimeError:
            # No event loop, create a new one
            asyncio.run(
                send_slack_alert(
                    message=message,
                    level="error",
                    trace_id=trace_id,
                    span_id=span_id,
                    metadata=metadata,
                )
            )


__all__ = ["send_slack_alert", "log_error_with_alert"]
