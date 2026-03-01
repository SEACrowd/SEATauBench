"""Name localization utility for airline domain.

This module provides functions to localize English names in task instructions
to their translated equivalents based on the database.
"""
import json
import re
from typing import Any, Dict, Optional

from tau2.domains.airline.utils import load_database_for_language


def build_name_mapping(language: Optional[str] = None) -> Dict[str, str]:
    """Build a mapping from English names to localized names.
    
    Args:
        language: Target language (e.g., "Thai"), or None for no mapping
        
    Returns:
        Dictionary mapping "FirstName LastName" to localized version
    """
    if language is None:
        return {}
    
    # Load database with language support
    db_data = load_database_for_language(language)
    users_data = db_data.get("users", [])
    
    name_mapping = {}
    
    for user_row in users_data:
        # Get English name
        name_field = user_row.get("name", "{}")
        if isinstance(name_field, str):
            try:
                name_dict = json.loads(name_field)
            except json.JSONDecodeError:
                continue
        else:
            name_dict = name_field
            
        english_first = name_dict.get("first_name", "").strip()
        english_last = name_dict.get("last_name", "").strip()
        
        if not english_first or not english_last:
            continue
        
        # Get localized name
        lang_field_name = f"name.{language}"
        localized_name_field = user_row.get(lang_field_name, "{}")
        
        if isinstance(localized_name_field, str):
            try:
                localized_name_dict = json.loads(localized_name_field)
            except json.JSONDecodeError:
                continue
        else:
            localized_name_dict = localized_name_field
            
        localized_first = localized_name_dict.get("first_name", "").strip()
        localized_last = localized_name_dict.get("last_name", "").strip()
        
        if not localized_first or not localized_last:
            continue
        
        # Create mapping entries
        english_full = f"{english_first} {english_last}"
        localized_full = f"{localized_first} {localized_last}"
        
        # Store various forms for flexible matching
        name_mapping[english_full] = localized_full
        name_mapping[english_first] = localized_first
        name_mapping[english_last] = localized_last
    
    return name_mapping


def localize_text(text: str, name_mapping: Dict[str, str]) -> str:
    """Localize names in text using the name mapping.
    
    Replaces English names with their localized equivalents while
    preserving the rest of the text structure.
    
    Args:
        text: Text to localize
        name_mapping: Dictionary mapping English names to localized names
        
    Returns:
        Text with names localized
    """
    if not text or not name_mapping:
        return text
    
    # Sort by length (longest first) to match full names before individual names
    sorted_names = sorted(name_mapping.keys(), key=len, reverse=True)
    
    result = text
    for english_name in sorted_names:
        localized_name = name_mapping[english_name]
        
        # Use word boundaries to avoid partial matches
        # But be careful with Unicode - use a simpler approach
        pattern = re.escape(english_name)
        result = re.sub(pattern, localized_name, result)
    
    return result


def localize_task_instructions(task_dict: Dict[str, Any], name_mapping: Dict[str, str]) -> Dict[str, Any]:
    """Localize names in task instructions.
    
    Args:
        task_dict: Task dictionary
        name_mapping: Name mapping dictionary
        
    Returns:
        Task dictionary with localized names
    """
    if not name_mapping:
        return task_dict
    
    # Localize user_scenario.instructions fields
    if "user_scenario" in task_dict and task_dict["user_scenario"]:
        user_scenario = task_dict["user_scenario"]
        
        if "instructions" in user_scenario and user_scenario["instructions"]:
            instructions = user_scenario["instructions"]
            
            # Localize known_info
            if "known_info" in instructions and instructions["known_info"]:
                instructions["known_info"] = localize_text(
                    instructions["known_info"], name_mapping
                )
            
            # Localize reason_for_call
            if "reason_for_call" in instructions and instructions["reason_for_call"]:
                instructions["reason_for_call"] = localize_text(
                    instructions["reason_for_call"], name_mapping
                )
            
            # Localize task_instructions
            if "task_instructions" in instructions and instructions["task_instructions"]:
                instructions["task_instructions"] = localize_text(
                    instructions["task_instructions"], name_mapping
                )
        
        # Localize persona if present
        if "persona" in user_scenario and user_scenario["persona"]:
            user_scenario["persona"] = localize_text(
                user_scenario["persona"], name_mapping
            )
    
    # Localize ticket if present
    if "ticket" in task_dict and task_dict["ticket"]:
        task_dict["ticket"] = localize_text(task_dict["ticket"], name_mapping)
    
    return task_dict
