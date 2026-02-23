from pathlib import Path
from typing import Optional

from tau2.utils.utils import DATA_DIR
from tau2.utils import load_file

AIRLINE_DATA_DIR = DATA_DIR / "tau2" / "domains" / "airline"
AIRLINE_DB_PATH = AIRLINE_DATA_DIR / "db.json"
AIRLINE_POLICY_PATH = AIRLINE_DATA_DIR / "policy.md"
AIRLINE_TASK_SET_PATH = AIRLINE_DATA_DIR / "tasks.json"


def get_language_db_path(language: Optional[str] = None, table: str = "users") -> Path:
    """Get the path to the language-specific database file.
    
    For the airline domain, translated DB files are in format:
    airline_db_merged_translated.xlsx - {table}.json
    
    Args:
        language: Target language (e.g., 'Thai', 'Chinese') or None for original
        table: Database table name (users, flights, reservations)
        
    Returns:
        Path to the database file
        
    Raises:
        FileNotFoundError: If the translated file doesn't exist
    """
    if language is None:
        return AIRLINE_DB_PATH
    
    # Translated files are split by table
    translated_file = AIRLINE_DATA_DIR / f"airline_db_merged_translated.xlsx - {table}.json"
    
    if not translated_file.exists():
        raise FileNotFoundError(
            f"Translated database file not found: {translated_file}. "
            f"Available languages for airline domain may be limited."
        )
    
    return translated_file


def load_merged_translated_db(language: Optional[str] = None) -> dict:
    """Load and merge all translated database tables.
    
    The airline translated DB is split into three files:
    - airline_db_merged_translated.xlsx - users.json (already nested dict format)
    - airline_db_merged_translated.xlsx - flights.json (flat array format)
    - airline_db_merged_translated.xlsx - reservations.json (flat array format)
    
    This function loads all three and merges them into the expected structure.
    
    Args:
        language: Target language or None for original db.json
        
    Returns:
        Merged dict with keys: users, flights, reservations
    """
    if language is None:
        # Load original db.json
        return load_file(AIRLINE_DB_PATH)
    
    # Load all three translated tables
    merged = {}
    
    # Users file is already in nested dict format: {"users": {"user_id": {...}}}
    users_path = get_language_db_path(language, "users")
    users_data = load_file(users_path)
    if isinstance(users_data, dict) and "users" in users_data:
        # Extract the nested users dict
        merged["users"] = users_data["users"]
    else:
        merged["users"] = users_data
    
    # Flights and reservations are flat arrays with _row_key
    for table in ["flights", "reservations"]:
        table_path = get_language_db_path(language, table)
        table_data = load_file(table_path)
        merged[table] = table_data
    
    return merged


def get_language_policy_path(language: Optional[str] = None) -> Path:
    """Get the path to the language-specific policy file.
    
    Args:
        language: Target language or None for original
        
    Returns:
        Path to the policy file
    """
    if language is None:
        return AIRLINE_POLICY_PATH
    
    # Check for translated policy files in multiple formats
    # Format 1: policy-{Language}.md (e.g., policy-Thai.md)
    translated_policy = AIRLINE_DATA_DIR / f"policy-{language}.md"
    if translated_policy.exists():
        return translated_policy
    
    # Format 2: policy_{language}.md (e.g., policy_Thai.md)
    translated_policy = AIRLINE_DATA_DIR / f"policy_{language}.md"
    if translated_policy.exists():
        return translated_policy
    
    # Fallback to original if translation doesn't exist
    return AIRLINE_POLICY_PATH


def get_language_tasks_path(language: Optional[str] = None) -> Path:
    """Get the path to the language-specific tasks file.
    
    Args:
        language: Target language or None for original
        
    Returns:
        Path to the tasks file
    """
    if language is None:
        return AIRLINE_TASK_SET_PATH
    
    # Check for translated tasks file
    translated_tasks = AIRLINE_DATA_DIR / f"tasks_{language}.json"
    
    if translated_tasks.exists():
        return translated_tasks
    
    # Fallback to original if translation doesn't exist
    return AIRLINE_TASK_SET_PATH
