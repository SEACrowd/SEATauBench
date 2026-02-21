# Copyright Sierra
from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.airline.data_model import FlightDB
from tau2.domains.airline.tools import AirlineTools
from tau2.domains.airline.utils import (
    get_language_policy_path,
    get_language_tasks_path,
    load_database_for_language,
)
from tau2.environment.db import TranslatedDBLoader
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(
    db: Optional[FlightDB] = None,
    solo_mode: bool = False,
    language: Optional[str] = None,
) -> Environment:
    """Get the airline environment with optional language support.
    
    Args:
        db: Optional pre-loaded database (for testing)
        solo_mode: Whether to run in solo mode (not supported for airline)
        language: Optional language for translated assets (e.g., "Thai", "Chinese")
                 If None, uses original English assets
    
    Returns:
        Configured airline environment
    
    Raises:
        ValueError: If solo_mode is True or language is not supported
    """
    if solo_mode:
        raise ValueError("Airline domain does not support solo mode")
    
    if db is None:
        # Load database with language support
        db_data = load_database_for_language(language)
        
        # Transform if needed (handles translated flat array format)
        if language:
            db_data = TranslatedDBLoader.transform_database(db_data, language)
        
        # Validate and create FlightDB instance
        db = FlightDB.model_validate(db_data)
    
    tools = AirlineTools(db)
    
    # Load policy with language support
    policy_path = get_language_policy_path(language)
    with open(policy_path, "r") as fp:
        policy = fp.read()
    
    return Environment(
        domain_name="airline",
        policy=policy,
        tools=tools,
    )


def get_tasks(
    task_split_name: Optional[str] = "base",
    language: Optional[str] = None,
) -> list[Task]:
    """Get tasks for the airline domain with optional language support.
    
    Args:
        task_split_name: Name of task split to load, or None for all tasks
        language: Optional language for translated tasks (e.g., "Thai")
    
    Returns:
        List of tasks
        
    Raises:
        ValueError: If task_split_name is invalid
    """
    # Load tasks with language support
    tasks_path = get_language_tasks_path(language)
    tasks = load_file(tasks_path)
    tasks = [Task.model_validate(task) for task in tasks]
    
    if task_split_name is None:
        return tasks
    
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. Valid splits are: {task_splits.keys()}"
        )
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    """Get task split definitions.
    
    Note: Task splits are language-independent (use task IDs)
    """
    from tau2.domains.airline.utils import AIRLINE_TASK_SET_PATH
    
    split_file = (
        Path(AIRLINE_TASK_SET_PATH).parent
        / f"split_{Path(AIRLINE_TASK_SET_PATH).stem}.json"
    )
    return load_file(split_file)
