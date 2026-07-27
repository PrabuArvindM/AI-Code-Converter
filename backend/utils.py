"""
Utility helpers for file handling, code cleaning, and metadata mapping in PyMorph AI.
Created By: Prabu Arvind M
"""

import re
from typing import Dict, Any

LANGUAGE_CONFIG: Dict[str, Dict[str, str]] = {
    "java": {
        "name": "Java",
        "extension": ".java",
        "monaco_id": "java",
        "mime": "text/x-java-source",
        "default_filename": "Main.java"
    },
    "c": {
        "name": "C",
        "extension": ".c",
        "monaco_id": "c",
        "mime": "text/x-csrc",
        "default_filename": "main.c"
    },
    "cpp": {
        "name": "C++",
        "extension": ".cpp",
        "monaco_id": "cpp",
        "mime": "text/x-c++src",
        "default_filename": "main.cpp"
    },
    "c++": {
        "name": "C++",
        "extension": ".cpp",
        "monaco_id": "cpp",
        "mime": "text/x-c++src",
        "default_filename": "main.cpp"
    },
    "embedded_c": {
        "name": "Embedded C",
        "extension": ".c",
        "monaco_id": "c",
        "mime": "text/x-csrc",
        "default_filename": "embedded_main.c"
    },
    "embedded c": {
        "name": "Embedded C",
        "extension": ".c",
        "monaco_id": "c",
        "mime": "text/x-csrc",
        "default_filename": "embedded_main.c"
    },
    "swift": {
        "name": "Swift",
        "extension": ".swift",
        "monaco_id": "swift",
        "mime": "text/x-swift",
        "default_filename": "main.swift"
    },
    "python": {
        "name": "Python",
        "extension": ".py",
        "monaco_id": "python",
        "mime": "text/x-python",
        "default_filename": "script.py"
    }
}

def clean_markdown_code_blocks(code: str) -> str:
    """
    Strips markdown code blocks (e.g. ```java ... ```) if included in AI output.
    """
    if not code:
        return ""
    
    # Strip leading/trailing whitespace
    code = code.strip()
    
    # Match ```lang ... ``` pattern
    pattern = r"^```[a-zA-C+\-#]*\n?(.*?)\n?```$"
    match = re.search(pattern, code, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # If starting with ``` but not properly closed, remove initial line
    if code.startswith("```"):
        lines = code.splitlines()
        if len(lines) > 1:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    return code

def get_language_info(target_language: str) -> Dict[str, str]:
    """
    Returns metadata for the requested target language.
    """
    key = target_language.lower().strip().replace(" ", "_")
    if key in LANGUAGE_CONFIG:
        return LANGUAGE_CONFIG[key]
    
    # Default fallback
    return {
        "name": target_language.capitalize(),
        "extension": ".txt",
        "monaco_id": "plaintext",
        "mime": "text/plain",
        "default_filename": f"converted_{key}.txt"
    }

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes user filename input to prevent directory traversal.
    """
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
