"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

import markdown as md
from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
import xml.etree.ElementTree as etree


extensions = [
    "markdown.extensions.tables",
    "markdown.extensions.toc",
    "pymdownx.magiclink",
    "pymdownx.betterem",
    "pymdownx.tilde",
    "pymdownx.emoji",
    "pymdownx.tasklist",
    "pymdownx.superfences",
    "pymdownx.saneheaders",
    "pymdownx.arithmatex",  # <--- ADD THIS for math support
]

extension_configs = {
    "markdown.extensions.toc": {
        "title": "Table of Contents",
        "permalink": False,
        "permalink_leading": True,
    },
    "pymdownx.magiclink": {
        "repo_url_shortener": True,
        "repo_url_shorthand": True,
        "provider": "github",
        "user": "facelessuser",
        "repo": "pymdown-extensions",
    },
    "pymdownx.tilde": {"subscript": False},
    "pymdownx.arithmatex": {  # <--- ADD THIS configuration
        "generic": True,  # Use generic mode for flexibility with MathJax/KaTeX
    },
}


import re
from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
import xml.etree.ElementTree as etree

# 1. THE EXTENSIVE DICTIONARY
EXTENDED_EMOTICONS = {
    # Happy / Smile
    ":-)": "🙂",
    ":)": "🙂",
    "=)": "🙂",
    ":]": "🙂",
    ":-]": "🙂",
    # Grinning / Laughing
    ":-D": "😃",
    ":D": "😃",
    "=D": "😃",
    "xD": "😆",
    "XD": "😆",
    "8-D": "😃",
    # Sad / Frowning
    ":-(": "🙁",
    ":(": "🙁",
    "=(": "🙁",
    ":[": "🙁",
    ":-[": "🙁",
    # Crying
    ":'(": "😢",
    ":'-(": "😢",
    # Wink
    ";-)": "😉",
    ";)": "😉",
    "*-)": "😉",
    "*)": "😉",
    ";-]": "😉",
    # Tongue Out (Playful)
    ":-P": "😛",
    ":P": "😛",
    "=P": "😛",
    ":-p": "😛",
    ":p": "😛",
    ":b": "😛",
    # Surprise / Shock
    ":-O": "😮",
    ":O": "😮",
    ":-o": "😮",
    ":o": "😮",
    "8-0": "😮",
    "=O": "😮",
    # Cool / Sunglasses
    "8-)": "😎",
    "B-)": "😎",
    "B)": "😎",
    # Love / Affection
    "<3": "❤️",
    "&lt;3": "❤️",  # Handle HTML escaped version just in case
    "</3": "💔",
    "&lt;/3": "💔",
    ":-*": "😘",
    ":*": "😘",
    # Confused / Skeptical / Annoyed
    # Note: We avoid ':/' because it breaks http:// URLs. We use ':-/' instead.
    ":-/": "😕",
    ":-\\": "😕",
    ":-|": "😐",
    ":|": "😐",
    # Angry
    ">:(": "😠",
    ">:-(": "😠",
    # Embarrassed / Blush
    ":$": "😳",
    ":-$": "😳",
    # Misc
    "O:-)": "😇",
    "0:-)": "😇",  # Angel
    ">:)": "😈",
    ">:-)": "😈",  # Devil
    "D:<": "😨",  # Horror
}


class EmoticonInlineProcessor(InlineProcessor):
    def __init__(self, pattern, md, emoticons):
        super().__init__(pattern, md)
        self.emoticons = emoticons

    def handleMatch(self, m, data):
        emoticon = m.group(1)
        # Handle case sensitivity for things like xD vs XD if needed,
        # but the dictionary keys usually handle it.
        emoji_char = self.emoticons.get(emoticon)

        if not emoji_char:
            # Fallback for HTML escaped variants if necessary
            emoji_char = self.emoticons.get(emoticon.replace("&lt;", "<"))

        if emoji_char:
            el = etree.Element("span")
            el.text = emoji_char
            el.set("class", "emoji")
            el.set("title", emoticon)  # Adds hover text showing original syntax
            return el, m.start(0), m.end(0)
        return None, None, None


class EmoticonExtension(Extension):
    def extendMarkdown(self, md):
        # 2. SORT BY LENGTH DESCENDING
        # Critical: Ensures ':-((' matches before ':-('
        sorted_keys = sorted(EXTENDED_EMOTICONS.keys(), key=len, reverse=True)

        # 3. BUILD REGEX
        # We escape the keys to handle characters like (, ), *, | safely
        pattern_str = (
            r"(" + "|".join(re.escape(k) for k in sorted_keys if len(k) > 2) + r")"
        )

        # 4. REGISTER
        # Priority 175 is generally safe.
        # If you find it breaking links (http://), lower it to < 120.
        md.inlinePatterns.register(
            EmoticonInlineProcessor(pattern_str, md, EXTENDED_EMOTICONS),
            "emoticons",
            175,
        )



# Initialize extensions ONCE at module level
markdown_extensions = extensions + [EmoticonExtension()]

# Create a global instance
_markdowner = md.Markdown(
    extensions=markdown_extensions, 
    extension_configs=extension_configs
)

def parse_markdown(data):
    """
    Returns HTML string.
    Note: We must reset the instance to clear state (like footnotes) between converts.
    """
    _markdowner.reset()
    html = _markdowner.convert(data)
    
    return html