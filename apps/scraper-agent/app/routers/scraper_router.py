"""Scraper routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.scraper_service import ScraperService

router = APIRouter()


class ScrapeRequest(BaseModel):
    url: str


@router.post("/scrape")
async def scrape(request: ScrapeRequest):
    try:
        service = ScraperService()
        result = await service.scrape_url(request.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

