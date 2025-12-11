"""Seed script for populating agent marketplace with example agents."""

from sqlmodel import Session
from uuid import uuid4
from .agent_marketplace_models import Agent
from .database import engine, init_db


def seed_agents(session: Session):
    """Seed the marketplace with example agents."""
    
    agents = [
        {
            "id": str(uuid4()),
            "name": "email-agent",
            "display_name": "Email Automation Agent",
            "description": "Automate email processing, responses, and management with AI-powered intelligence.",
            "version": "1.0.0",
            "category": "automation",
            "author": "AI Automation Platform",
            "config_schema": {
                "type": "object",
                "properties": {
                    "api_key": {
                        "type": "string",
                        "title": "API Key",
                        "description": "Email service API key",
                        "format": "password"
                    },
                    "email_address": {
                        "type": "string",
                        "title": "Email Address",
                        "description": "Email address to monitor",
                        "format": "email"
                    },
                    "check_interval": {
                        "type": "integer",
                        "title": "Check Interval (minutes)",
                        "description": "How often to check for new emails",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 60
                    },
                    "auto_reply": {
                        "type": "boolean",
                        "title": "Enable Auto-Reply",
                        "description": "Automatically reply to emails",
                        "default": False
                    },
                    "target_folders": {
                        "type": "array",
                        "title": "Target Folders",
                        "description": "Folders to monitor (one per line)",
                        "items": {"type": "string"}
                    }
                },
                "required": ["api_key", "email_address"]
            },
            "required_tools": ["send_email", "read_email", "search_email"],
            "default_tasks": {
                "tasks": [
                    {
                        "name": "process_pending_emails",
                        "description": "Process pending emails every 5 minutes",
                        "enabled": True,
                        "type": "interval",
                        "schedule": "5 minutes",
                        "function": "app.services.email_service:process_pending_emails_task",
                        "kwargs": {
                            "batch_size": 10
                        }
                    },
                    {
                        "name": "send_digest",
                        "description": "Send daily email digest at 8 AM",
                        "enabled": True,
                        "type": "cron",
                        "schedule": "0 8 * * *",
                        "function": "app.services.email_service:send_digest_task"
                    }
                ]
            },
            "tags": ["email", "automation", "communication"],
            "is_active": True
        },
        {
            "id": str(uuid4()),
            "name": "aiops-bot",
            "display_name": "AIOps Monitoring Bot",
            "description": "Monitor system health, detect anomalies, and automate incident response.",
            "version": "1.0.0",
            "category": "monitoring",
            "author": "AI Automation Platform",
            "config_schema": {
                "type": "object",
                "properties": {
                    "monitoring_endpoints": {
                        "type": "array",
                        "title": "Monitoring Endpoints",
                        "description": "URLs to monitor (one per line)",
                        "items": {"type": "string", "format": "uri"}
                    },
                    "alert_webhook": {
                        "type": "string",
                        "title": "Alert Webhook URL",
                        "description": "Webhook URL for sending alerts",
                        "format": "uri"
                    },
                    "check_interval": {
                        "type": "integer",
                        "title": "Check Interval (seconds)",
                        "description": "How often to check endpoints",
                        "default": 60,
                        "minimum": 10,
                        "maximum": 3600
                    },
                    "threshold_cpu": {
                        "type": "number",
                        "title": "CPU Threshold (%)",
                        "description": "Alert if CPU usage exceeds this",
                        "default": 80,
                        "minimum": 0,
                        "maximum": 100
                    },
                    "threshold_memory": {
                        "type": "number",
                        "title": "Memory Threshold (%)",
                        "description": "Alert if memory usage exceeds this",
                        "default": 85,
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["monitoring_endpoints"]
            },
            "required_tools": ["check_endpoint", "send_alert", "get_metrics"],
            "default_tasks": {
                "tasks": [
                    {
                        "name": "health_check",
                        "description": "Perform health checks every minute",
                        "enabled": True,
                        "type": "interval",
                        "schedule": "1 minute",
                        "function": "app.services.aiops_service:health_check_task"
                    },
                    {
                        "name": "daily_report",
                        "description": "Generate daily report at 9 AM",
                        "enabled": True,
                        "type": "cron",
                        "schedule": "0 9 * * *",
                        "function": "app.services.aiops_service:generate_report_task"
                    }
                ]
            },
            "tags": ["monitoring", "ops", "alerts"],
            "is_active": True
        },
        {
            "id": str(uuid4()),
            "name": "support-bot",
            "display_name": "Customer Support Bot",
            "description": "AI-powered customer support agent that handles tickets and provides intelligent responses.",
            "version": "1.0.0",
            "category": "support",
            "author": "AI Automation Platform",
            "config_schema": {
                "type": "object",
                "properties": {
                    "support_email": {
                        "type": "string",
                        "title": "Support Email",
                        "description": "Email address for support tickets",
                        "format": "email"
                    },
                    "api_key": {
                        "type": "string",
                        "title": "Support API Key",
                        "description": "API key for support system",
                        "format": "password"
                    },
                    "response_timeout": {
                        "type": "integer",
                        "title": "Response Timeout (hours)",
                        "description": "Maximum time to respond to tickets",
                        "default": 24,
                        "minimum": 1,
                        "maximum": 168
                    },
                    "escalation_threshold": {
                        "type": "integer",
                        "title": "Escalation Threshold",
                        "description": "Number of failed auto-responses before escalation",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    },
                    "knowledge_base_id": {
                        "type": "string",
                        "title": "Knowledge Base ID",
                        "description": "ID of the knowledge base to use"
                    }
                },
                "required": ["support_email", "api_key"]
            },
            "required_tools": ["create_ticket", "update_ticket", "search_knowledge"],
            "default_tasks": {
                "tasks": [
                    {
                        "name": "process_tickets",
                        "description": "Process new support tickets every 10 minutes",
                        "enabled": True,
                        "type": "interval",
                        "schedule": "10 minutes",
                        "function": "app.services.support_service:process_tickets_task"
                    }
                ]
            },
            "tags": ["support", "customer-service", "tickets"],
            "is_active": True
        },
        {
            "id": str(uuid4()),
            "name": "scraper-agent",
            "display_name": "Web Scraper Agent",
            "description": "Intelligent web scraping agent that extracts and monitors web content.",
            "version": "1.0.0",
            "category": "automation",
            "author": "AI Automation Platform",
            "config_schema": {
                "type": "object",
                "properties": {
                    "target_urls": {
                        "type": "array",
                        "title": "Target URLs",
                        "description": "URLs to scrape (one per line)",
                        "items": {"type": "string", "format": "uri"}
                    },
                    "scrape_interval": {
                        "type": "integer",
                        "title": "Scrape Interval (hours)",
                        "description": "How often to scrape",
                        "default": 24,
                        "minimum": 1,
                        "maximum": 168
                    },
                    "user_agent": {
                        "type": "string",
                        "title": "User Agent",
                        "description": "User agent string to use",
                        "default": "Mozilla/5.0"
                    },
                    "respect_robots_txt": {
                        "type": "boolean",
                        "title": "Respect robots.txt",
                        "description": "Follow robots.txt rules",
                        "default": True
                    },
                    "output_format": {
                        "type": "string",
                        "title": "Output Format",
                        "description": "Format for scraped data",
                        "enum": ["json", "csv", "html"],
                        "default": "json"
                    }
                },
                "required": ["target_urls"]
            },
            "required_tools": ["scrape_url", "parse_html", "save_data"],
            "default_tasks": {
                "tasks": [
                    {
                        "name": "scrape_targets",
                        "description": "Scrape target URLs daily",
                        "enabled": True,
                        "type": "cron",
                        "schedule": "0 2 * * *",
                        "function": "app.services.scraper_service:scrape_targets_task"
                    }
                ]
            },
            "tags": ["scraping", "data-extraction", "monitoring"],
            "is_active": True
        },
        {
            "id": str(uuid4()),
            "name": "rag-chat",
            "display_name": "RAG Chat Agent",
            "description": "Retrieval-Augmented Generation chat agent with knowledge base integration.",
            "version": "1.0.0",
            "category": "chat",
            "author": "AI Automation Platform",
            "config_schema": {
                "type": "object",
                "properties": {
                    "knowledge_base_id": {
                        "type": "string",
                        "title": "Knowledge Base ID",
                        "description": "ID of the knowledge base to use"
                    },
                    "model": {
                        "type": "string",
                        "title": "LLM Model",
                        "description": "Language model to use",
                        "enum": ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"],
                        "default": "gpt-3.5-turbo"
                    },
                    "temperature": {
                        "type": "number",
                        "title": "Temperature",
                        "description": "Model temperature (0-1)",
                        "default": 0.7,
                        "minimum": 0,
                        "maximum": 1
                    },
                    "max_tokens": {
                        "type": "integer",
                        "title": "Max Tokens",
                        "description": "Maximum tokens in response",
                        "default": 1000,
                        "minimum": 100,
                        "maximum": 4000
                    },
                    "top_k": {
                        "type": "integer",
                        "title": "Top K Results",
                        "description": "Number of knowledge base results to retrieve",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["knowledge_base_id"]
            },
            "required_tools": ["search_knowledge", "generate_response"],
            "default_tasks": {
                "tasks": [
                    {
                        "name": "update_embeddings",
                        "description": "Update knowledge base embeddings daily",
                        "enabled": True,
                        "type": "cron",
                        "schedule": "0 3 * * *",
                        "function": "app.services.rag_service:update_embeddings_task"
                    }
                ]
            },
            "tags": ["chat", "rag", "knowledge-base"],
            "is_active": True
        }
    ]

    for agent_data in agents:
        from sqlmodel import select
        existing = session.exec(
            select(Agent).where(Agent.name == agent_data["name"])
        ).first()
        if not existing:
            agent = Agent(**agent_data)
            session.add(agent)
            print(f"Added agent: {agent_data['name']}")
        else:
            print(f"Agent already exists: {agent_data['name']}")

    session.commit()


if __name__ == "__main__":
    from sqlmodel import Session
    
    # Initialize database
    init_db()
    
    with Session(engine) as session:
        seed_agents(session)
        print("Agent marketplace seeded successfully!")
