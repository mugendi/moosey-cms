"""
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
"""
import os
import re

def make_asset_normalizer(static_dir: str):
    """
    static_dir can be a bare name ("static") or a full absolute
    filesystem path (e.g. "/media/.../backhome-construction/static").
    Either way, incoming asset paths may reference it via:
      - the full absolute path
      - just the basename ("static" / "/static")
      - or already be normalized ("/images/...")
    """
    static_dir = static_dir.rstrip('/')
    static_name = os.path.basename(static_dir)  # e.g. "static"

    # Longest-prefix-first: try the full absolute path, then just the name.
    candidates = sorted({static_dir, static_name}, key=len, reverse=True)
    alternation = '|'.join(re.escape(c) for c in candidates)
    pattern = re.compile(rf'^/?(?:{alternation})/')

    def normalize(path: str) -> str:
        p = pattern.sub('', path, count=1).strip('/')
        if not p:
            raise ValueError(f"empty asset path after normalization: {path!r}")
        return f'/{p}'

    return normalize
