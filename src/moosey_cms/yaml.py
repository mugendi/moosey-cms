"""
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
"""

"""
Load and parse YAML data with ruamel.yaml.
Install: uv pip install ruamel.yaml
"""

from ruamel.yaml import YAML
from pathlib import Path
from io import StringIO


# ============================================
# LOAD FROM FILE
# ============================================

def load_yaml_file(filepath: str | Path) -> dict | list:
    """
    Load YAML data from file path.
    
    Args:
        filepath: Path to YAML file
    
    Returns:
        Parsed YAML as Python dict/list
    """
    yaml = YAML()
    yaml.preserve_quotes = True      # Keep original quotes
    yaml.default_flow_style = False  # Use block style
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.load(f)
    
    return data


# ============================================
# LOAD FROM STRING
# ============================================

def load_yaml_string(content: str) -> dict | list:
    """
    Parse YAML from string.
    
    Args:
        content: YAML string content
    
    Returns:
        Parsed YAML as Python dict/list
    """
    yaml = YAML()
    
    return yaml.load(StringIO(content))


# ============================================
# LOAD WITH COMMENTS PRESERVED (ROUND-TRIP)
# ============================================

def load_yaml_roundtrip(filepath: str | Path):
    """
    Load YAML preserving comments and formatting for editing.
    Returns a CommentedMap/CommentedList that can be modified and saved back.
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.load(f)
    
    return data, yaml  # Return data and YAML instance for dumping


def save_yaml_roundtrip(data, yaml: YAML, filepath: str | Path) -> None:
    """
    Save YAML back to file preserving comments and formatting.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(data, f)


# ============================================
# LOAD MULTIPLE DOCUMENTS
# ============================================

def load_yaml_multi(content: str) -> list:
    """
    Load multiple YAML documents separated by '---'.
    
    Args:
        content: Multi-document YAML string
    
    Returns:
        List of parsed documents
    """
    yaml = YAML()
    
    documents = list(yaml.load_all(StringIO(content)))
    return documents


# ============================================
# SAFE LOAD (DISABLED CONSTRUCTORS)
# ============================================

def load_yaml_safe(content: str) -> dict | list:
    """
    Load YAML safely without executing arbitrary code.
    ruamel.yaml is safe by default (no !!python/object execution).
    """
    yaml = YAML(typ="safe")  # Explicit safe mode
    yaml.default_flow_style = False
    
    return yaml.load(StringIO(content))


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    # From string
    yaml_content = """
    name: Alice
    age: 30
    address:
      city: NYC
      zip: "10001"
    hobbies:
      - reading
      - coding
    """
    
    data = load_yaml_string(yaml_content)
    print(f"Name: {data['name']}")
    print(f"City: {data['address']['city']}")
    print(f"Hobbies: {data['hobbies']}")
    
    # Multi-document
    multi = """
    ---
    id: 1
    ---
    id: 2
    """
    docs = load_yaml_multi(multi)
    print(f"Documents: {len(docs)}")
    
    # Round-trip with file
    # data, yaml = load_yaml_roundtrip("config.yaml")
    # data["new_key"] = "value"
    # save_yaml_roundtrip(data, yaml, "config.yaml")