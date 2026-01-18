"""
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
"""

from pathlib import Path
from pydantic import BaseModel, RootModel, HttpUrl, EmailStr, Field, field_validator, HttpUrl
from typing import List, Optional, Union, Dict, Any



class Dirs(BaseModel):
    content: Path
    templates: Path

    @field_validator('content', 'templates', mode='before')
    @classmethod
    def resolve_path(cls, v):
        if isinstance(v, str):
            v = Path(v)
        return v.resolve()

    @field_validator('content', 'templates')
    @classmethod
    def must_exist(cls, v: Path):
        if not v.exists():
            raise ValueError(f'Path does not exist: {v}')
        return v


class OpenGraph(BaseModel):
    og_image : str

class SiteData(BaseModel):
    name: Optional[str] = None
    keywords: Optional[list[str]] = None
    description: Optional[str] = None
    author: Optional[str] = None
    social: Optional[Dict[str, HttpUrl]] = None
    open_graph: Optional[OpenGraph]


class SiteCode(RootModel[Dict[str, str]]):
    root: Dict[str, Any]