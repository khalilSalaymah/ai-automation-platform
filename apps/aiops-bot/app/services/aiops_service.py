"""AIOps service."""

from core import LLM
from ..agents.aiops_agent import AiOpsAgent
from ..config import settings


class AiOpsService:
    def __init__(self):
        # LLM will auto-detect provider from LLM_PROVIDER env var
        # For Groq apps, set LLM_PROVIDER=groq and GROQ_API_KEY
        self.llm = LLM(model="llama3-8b-8192")
        self.agent = AiOpsAgent(name="aiops-agent", llm=self.llm)

    async def analyze(self, query: str, metrics: dict):
        result = self.agent.act({"query": query, "metrics": metrics})
        return {"analysis": result.get("response", ""), "recommendations": result.get("recommendations", [])}


# Scheduled task functions (must be synchronous for RQ)
def analyze_metrics_task(metrics_source: str = "prometheus") -> dict:
    """
    Scheduled task to analyze system metrics.
    
    Args:
        metrics_source: Source of metrics data
        
    Returns:
        Result dictionary
    """
    from core.logger import logger
    from core.event_bus import EventBus
    
    logger.info(f"Analyzing metrics from {metrics_source}")
    # TODO: Implement actual metrics analysis
    
    event_bus = EventBus()
    event_bus.publish(
        event_type="aiops.metrics_analyzed",
        source_agent="aiops-bot",
        payload={"source": metrics_source}
    )
    
    return {"status": "success", "source": metrics_source}


def generate_report_task() -> dict:
    """
    Scheduled task to generate daily AIOps report.
    
    Returns:
        Result dictionary
    """
    from core.logger import logger
    from datetime import datetime
    
    logger.info("Generating daily AIOps report")
    # TODO: Implement actual report generation
    
    return {"status": "success", "report_generated": True, "date": datetime.utcnow().isoformat()}


def check_alerts_task() -> dict:
    """
    Scheduled task to check and process alerts.
    
    Returns:
        Result dictionary
    """
    from core.logger import logger
    from core.event_bus import EventBus
    
    logger.info("Checking alerts")
    # TODO: Implement actual alert checking
    
    event_bus = EventBus()
    event_bus.publish(
        event_type="aiops.alerts_checked",
        source_agent="aiops-bot",
        payload={"alerts_found": 0}
    )
    
    return {"status": "success", "alerts_checked": True}
