from pathlib import Path
from typing import Any, Dict, Optional

from tau2.utils import load_file
from tau2.utils.utils import DATA_DIR

AIRLINE_DATA_DIR = DATA_DIR / "tau2" / "domains" / "airline"
AIRLINE_DB_PATH = AIRLINE_DATA_DIR / "db.json"
AIRLINE_POLICY_PATH = AIRLINE_DATA_DIR / "policy.md"
AIRLINE_TASK_SET_PATH = AIRLINE_DATA_DIR / "tasks.json"

# Supported languages for airline domain
SUPPORTED_LANGUAGES = ["Chinese", "Indonesian", "Thai", "Vietnamese"]


def load_database_for_language(language: Optional[str] = None) -> Dict[str, Any]:
    """Load database data for the specified language.
    
    For original (language=None): loads unified db.json
    For translated: loads separate table files and combines them
    
    Args:
        language: Target language, or None for original
        
    Returns:
        Database data dict with structure: {table_name: table_data}
    """
    if language is None:
        # Load original unified database
        return load_file(AIRLINE_DB_PATH)
    
    # Load translated database (split by table)
    paths = get_language_db_paths(language)
    
    # Combine all tables into one dict
    db_data = {}
    for table_name, path in paths.items():
        db_data[table_name] = load_file(path)
    
    return db_data


def get_language_db_paths(language: Optional[str] = None) -> dict[str, Path]:
    """Get database file paths for the specified language.
    
    Args:
        language: Target language (e.g., "Thai"), or None for original
        
    Returns:
        Dict mapping table names to file paths
        
    Raises:
        ValueError: If language is not supported or files don't exist
    """
    if language is None:
        # Return original db.json path (not split by table)
        return {"db": AIRLINE_DB_PATH}
    
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Language '{language}' not supported for airline domain. "
            f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    
    # Translated files are split by table
    table_names = ["flights", "users", "reservations"]
    paths = {}
    
    for table in table_names:
        # Pattern: airline_db_merged_translated.xlsx - {table}.json
        path = AIRLINE_DATA_DIR / f"airline_db_merged_translated.xlsx - {table}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Translated database file not found: {path}. "
                f"Please ensure translations are generated for language '{language}'."
            )
        paths[table] = path
    
    return paths


def get_language_policy_path(language: Optional[str] = None) -> Path:
    """Get policy file path for the specified language.
    
    Args:
        language: Target language, or None for original
        
    Returns:
        Path to policy file
        
    Note:
        Falls back to original policy if translated version doesn't exist
    """
    if language is None:
        return AIRLINE_POLICY_PATH
    
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Language '{language}' not supported. "
            f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    
    # Try translated policy file
    translated_path = AIRLINE_DATA_DIR / f"policy_{language.lower()}.md"
    if translated_path.exists():
        return translated_path
    
    # Fall back to original if translated version doesn't exist
    # TODO: Log warning when falling back
    return AIRLINE_POLICY_PATH


def get_language_tasks_path(language: Optional[str] = None) -> Path:
    """Get tasks file path for the specified language.
    
    Args:
        language: Target language, or None for original
        
    Returns:
        Path to tasks file
        
    Note:
        Falls back to original tasks if translated version doesn't exist
    """
    if language is None:
        return AIRLINE_TASK_SET_PATH
    
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Language '{language}' not supported. "
            f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    
    # Try translated tasks file
    translated_path = AIRLINE_DATA_DIR / f"tasks_{language.lower()}.json"
    if translated_path.exists():
        return translated_path
    
    # Fall back to original if translated version doesn't exist
    # TODO: Log warning when falling back
    return AIRLINE_TASK_SET_PATH

