# Copyright Sierra
from pathlib import Path
from typing import Optional

from loguru import logger

from tau2.data_model.tasks import Task
from tau2.domains.airline.data_model import FlightDB
from tau2.domains.airline.name_localizer import (
    build_name_mapping,
    localize_task_instructions,
)
from tau2.domains.airline.tools import AirlineTools
from tau2.domains.airline.utils import (
    AIRLINE_DB_PATH,
    AIRLINE_POLICY_PATH,
    AIRLINE_TASK_SET_PATH,
    load_merged_translated_db,
    get_language_policy_path,
    get_language_tasks_path,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(
    db: Optional[FlightDB] = None,
    solo_mode: bool = False,
    language: Optional[str] = None,
) -> Environment:
    """Get the airline domain environment.

    Args:
        db: Optional pre-loaded database. If None, loads from file.
        solo_mode: Whether to run in solo mode (not supported for airline)
        language: Language for domain assets (e.g., 'Thai', 'Chinese'). None for original/English.

    Returns:
        Configured Environment instance

    Raises:
        ValueError: If solo_mode is True (not supported)
    """
    if solo_mode:
        raise ValueError("Airline domain does not support solo mode")
    if db is None:
        # Load merged translated database
        merged_data = load_merged_translated_db(language)
        # DB.load will handle flat-to-nested conversion and language field selection
        db = FlightDB.load(AIRLINE_DB_PATH, language=language)
        # Override with merged data since we manually loaded it
        from tau2.environment.db import TranslatedDBLoader

        if TranslatedDBLoader.is_flat_array_format(merged_data):
            merged_data = TranslatedDBLoader.convert_flat_to_nested(
                merged_data, language
            )
        db = FlightDB.model_validate(merged_data)

    tools = AirlineTools(db)

    # Load policy in appropriate language
    policy_path = get_language_policy_path(language)
    with open(policy_path, "r") as fp:
        policy = fp.read()

    return Environment(
        domain_name="airline",
        policy=policy,
        tools=tools,
    )


def get_tasks(
    task_split_name: Optional[str] = "base", language: Optional[str] = None
) -> list[Task]:
    """Get tasks for the airline domain.

    Args:
        task_split_name: Name of the task split to load
        language: Language for tasks (e.g., 'Thai', 'Chinese'). None for original/English.

    Returns:
        List of Task objects
    """
    tasks_path = get_language_tasks_path(language)
    tasks = load_file(tasks_path)
    tasks = [Task.model_validate(task) for task in tasks]
    
    # Apply name localization if language is specified
    if language is not None:
        name_mapping = build_name_mapping(language)
        localized_tasks = []
        for task in tasks:
            task_dict = task.model_dump()
            localized_task_dict = localize_task_instructions(task_dict, name_mapping)
            localized_tasks.append(Task.model_validate(localized_task_dict))
        tasks = localized_tasks
    
    if task_split_name is None:
        return tasks
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. Valid splits are: {task_splits.keys()}"
        )
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    split_file = (
        Path(AIRLINE_TASK_SET_PATH).parent
        / f"split_{Path(AIRLINE_TASK_SET_PATH).stem}.json"
    )
    return load_file(split_file)
