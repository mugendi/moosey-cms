"""
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Literal, Optional
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
    name: Optional[str] = Field(..., description="Site name")
    keywords: Optional[list[str]] = Field(..., description="SEO keywords")
    description: Optional[str] = Field(..., description="Site description")
    author: Optional[str] = Field(..., description="Site author")
    open_graph: Optional[OpenGraphConfig] = Field(..., description="Open Graph configuration")
    social: Optional[SocialConfig] = Field(..., description="Social media links")



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
    # site_code: Optional[SiteCode] = Field(..., description="Custom site code")
