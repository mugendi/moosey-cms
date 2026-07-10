"""
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Literal, Optional, Union
from pathlib import Path


class OpenGraphConfig(BaseModel):
    """Open Graph metadata configuration"""
    og_image: str = Field(..., description="Path to Open Graph image")
    og_title: Optional[str] = Field(None, description="Open Graph title")
    og_description: Optional[str] = Field(None, description="Open Graph description")
    og_url: Optional[str] = Field(None, description="Open Graph URL")
 
 
class SocialConfig(BaseModel):
    """Social media links configuration"""
    twitter: Optional[str] = Field(None, description="Twitter/X profile URL")
    facebook: Optional[str] = Field(None, description="Facebook profile URL")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    instagram: Optional[str] = Field(None, description="Instagram profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
 
    @field_validator('twitter', 'facebook', 'linkedin', 'instagram', 'github')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Social media links must be valid URLs starting with http:// or https://')
        return v
 
 
class SiteData(BaseModel):
    """Site metadata and configuration"""
    name: Optional[str] = Field(None, description="Site name")
    keywords: list[str] = Field(default_factory=list, description="SEO keywords")
    description: Optional[str] = Field(None, description="Site description")
    author: Optional[str] = Field(None, description="Site author")
    open_graph: Optional[OpenGraphConfig] = Field(None, description="Open Graph configuration")
    social: Optional[SocialConfig] = Field(None, description="Social media links")
 
 
 
class Dirs(BaseModel):
    """Directory paths configuration"""
    content: Path = Field(..., description="Content directory path")
    templates: Path = Field(..., description="Templates directory path")
 
    @field_validator('content', 'templates')
    @classmethod
    def validate_path_exists(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f'Directory does not exist: {v}')
        if not v.is_dir():
            raise ValueError(f'Path is not a directory: {v}')
        return v
 
 
class CMSConfig(BaseModel):
    """Complete CMS initialization configuration"""
    host: str = Field(..., description="Server host address")
    port: int = Field(..., ge=1, le=65535, description="Server port number")
    dirs: Dirs = Field(..., description="Directory configuration")
    mode: Literal["development", "production", "staging", "testing"] = Field(
        ..., 
        description="Application mode"
    )
    site_data: Optional[SiteData] = Field(..., description="Site metadata")
    reload_delay: float = Field(
        default=0,
        ge=0,
        description=(
            "Seconds to wait before sending the hot-reload signal to connected "
            "browsers. Useful when a build step runs after a file change and you "
            "want the browser to wait until the build has finished before "
            "refreshing. Only has an effect in development mode."
        ),
    )
    admin: Optional[Union[str, dict]] = Field(
        default=None,
        description=(
            "Admin content-editing configuration. Can be a string prefix "
            "(e.g. 'admin/content') for backward compatibility, or a dict "
            "with keys: 'prefix' (route prefix) and 'templates' (subdirectory "
            "within templates/ for admin templates, default 'admin')."
        ),
    )

    @field_validator("admin")
    @classmethod
    def validate_admin(cls, v):
        if v is None:
            return None
        # Backward compat: string -> dict
        if isinstance(v, str):
            v = v.strip().strip("/")
            if not v:
                return None
            return {"prefix": v, "templates": "admin"}
        if not isinstance(v, dict):
            raise ValueError("admin must be a string or dict")
        if "prefix" not in v:
            raise ValueError("admin dict must contain a 'prefix' key")
        v["prefix"] = v["prefix"].strip().strip("/")
        if not v["prefix"]:
            raise ValueError("admin prefix cannot be empty")
        v.setdefault("templates", "admin")
        v["templates"] = v["templates"].strip("/").strip()
        if not v["templates"]:
            v["templates"] = "admin"
        return v