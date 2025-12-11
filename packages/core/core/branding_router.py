"""Branding router for white-label configuration."""

import uuid
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from pydantic import BaseModel

from .database import get_session
from .models import Organization, User
from .dependencies import get_current_active_user, get_user_org_id
from .config import get_settings

settings = get_settings()
router = APIRouter(prefix="/branding", tags=["branding"])

# Create upload directory for branding assets
UPLOAD_DIR = Path(tempfile.gettempdir()) / "branding_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ThemeVariables(BaseModel):
    """Theme variables model."""

    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    font_family: Optional[str] = None
    font_size_base: Optional[str] = None
    border_radius: Optional[str] = None


class BrandingSettings(BaseModel):
    """Branding settings model."""

    logo_url: Optional[str] = None
    custom_domain: Optional[str] = None
    theme_variables: Optional[ThemeVariables] = None


class BrandingSettingsResponse(BaseModel):
    """Branding settings response model."""

    logo_url: Optional[str] = None
    custom_domain: Optional[str] = None
    theme_variables: Optional[dict] = None


@router.get("/settings", response_model=BrandingSettingsResponse)
async def get_branding_settings(
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
    session: Session = Depends(get_session),
):
    """Get branding settings for the current organization."""
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    organization = session.get(Organization, org_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return BrandingSettingsResponse(
        logo_url=organization.logo_url,
        custom_domain=organization.custom_domain,
        theme_variables=organization.theme_variables or {},
    )


@router.put("/settings", response_model=BrandingSettingsResponse)
async def update_branding_settings(
    settings: BrandingSettings,
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
    session: Session = Depends(get_session),
):
    """Update branding settings for the current organization."""
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    organization = session.get(Organization, org_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Update logo URL if provided
    if settings.logo_url is not None:
        organization.logo_url = settings.logo_url

    # Update custom domain if provided
    if settings.custom_domain is not None:
        # Validate domain format
        if settings.custom_domain and not _is_valid_domain(settings.custom_domain):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid domain format",
            )
        
        # Check if domain is already taken by another organization
        if settings.custom_domain:
            existing_org = session.exec(
                select(Organization).where(
                    Organization.custom_domain == settings.custom_domain,
                    Organization.id != org_id,
                )
            ).first()
            if existing_org:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Domain already in use by another organization",
                )
        
        organization.custom_domain = settings.custom_domain

    # Update theme variables if provided
    if settings.theme_variables is not None:
        theme_dict = settings.theme_variables.dict(exclude_none=True)
        organization.theme_variables = theme_dict if theme_dict else None

    session.add(organization)
    session.commit()
    session.refresh(organization)

    return BrandingSettingsResponse(
        logo_url=organization.logo_url,
        custom_domain=organization.custom_domain,
        theme_variables=organization.theme_variables or {},
    )


@router.post("/logo/upload")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
    session: Session = Depends(get_session),
):
    """Upload a logo for the organization."""
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/svg+xml", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}",
        )

    # Validate file size (max 5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit",
        )

    # Generate unique filename
    file_extension = Path(file.filename).suffix if file.filename else ".png"
    file_id = str(uuid.uuid4())
    filename = f"{org_id}_{file_id}{file_extension}"
    file_path = UPLOAD_DIR / filename

    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )

    # Update organization logo URL
    organization = session.get(Organization, org_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Generate URL (in production, this should be a proper CDN or static file URL)
    logo_url = f"/api/branding/logo/{filename}"
    organization.logo_url = logo_url

    session.add(organization)
    session.commit()

    return {"logo_url": logo_url, "filename": filename}


@router.get("/logo/{filename}")
async def get_logo(
    filename: str,
):
    """Get logo file (public endpoint)."""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logo not found",
        )

    # Determine content type from extension
    content_type = "image/png"
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        content_type = "image/jpeg"
    elif filename.endswith(".svg"):
        content_type = "image/svg+xml"
    elif filename.endswith(".gif"):
        content_type = "image/gif"
    elif filename.endswith(".webp"):
        content_type = "image/webp"

    return FileResponse(
        path=file_path,
        media_type=content_type,
    )


@router.delete("/logo")
async def delete_logo(
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
    session: Session = Depends(get_session),
):
    """Delete organization logo."""
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    organization = session.get(Organization, org_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Delete file if exists
    if organization.logo_url:
        # Extract filename from URL
        filename = organization.logo_url.split("/")[-1]
        file_path = UPLOAD_DIR / filename
        if file_path.exists():
            file_path.unlink()

    organization.logo_url = None
    session.add(organization)
    session.commit()

    return {"message": "Logo deleted successfully"}


def _is_valid_domain(domain: str) -> bool:
    """Validate domain format."""
    import re
    # Basic domain validation
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))
