from typing import Any, Optional
import json

from tau2.utils import dump_file, get_pydantic_hash, load_file
from tau2.utils.pydantic_utils import BaseModelNoExtra


class TranslatedDBLoader:
    """Loader for translated database files with language-specific fields.
    
    Converts flat array format (from Excel translation) back to nested dict structure.
    """
    
    @staticmethod
    def is_flat_array_format(data: Any) -> bool:
        """Check if data is in flat array format (has _row_key field).
        
        Args:
            data: The loaded data to check
            
        Returns:
            True if data is in flat array format
        """
        if isinstance(data, dict):
            # Check if it's a dict of tables (e.g., {"users": [...], "flights": [...]})
            for value in data.values():
                if isinstance(value, list) and len(value) > 0:
                    if isinstance(value[0], dict) and "_row_key" in value[0]:
                        return True
        elif isinstance(data, list) and len(data) > 0:
            # Check if it's a single table array
            if isinstance(data[0], dict) and "_row_key" in data[0]:
                return True
        return False
    
    @staticmethod
    def parse_json_field(value: Any) -> Any:
        """Parse JSON-encoded string fields.
        
        Args:
            value: The field value to parse
            
        Returns:
            Parsed JSON object if string, otherwise original value
        """
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                # Not JSON, return as-is
                return value
        return value
    
    @staticmethod
    def select_language_field(row: dict, field_name: str, language: Optional[str]) -> Any:
        """Select the appropriate field value based on language.
        
        Args:
            row: The row dict
            field_name: Base field name (e.g., "name")
            language: Target language (e.g., "Thai") or None for original
            
        Returns:
            The field value in the target language, with JSON parsing applied
        """
        if language:
            # Try language-specific field first
            lang_field = f"{field_name}.{language}"
            if lang_field in row and row[lang_field] is not None:
                return TranslatedDBLoader.parse_json_field(row[lang_field])
        
        # Fallback to original field
        if field_name in row:
            return TranslatedDBLoader.parse_json_field(row[field_name])
        
        return None
    
    @staticmethod
    def convert_flat_to_nested(data: Any, language: Optional[str] = None) -> dict:
        """Convert flat array format with language fields to nested dict format.
        
        Args:
            data: The loaded data (dict of tables or single table array)
            language: Target language for field selection
            
        Returns:
            Nested dict structure: {"table_name": {"entity_id": {...}}}
        """
        result = {}
        
        # Handle different input formats
        if isinstance(data, dict):
            # Dict of tables: {"users": [...], "flights": [...]} OR {"users": {...already nested...}}
            tables = data
        elif isinstance(data, list):
            # Single table array - use "data" as table name
            tables = {"data": data}
        else:
            raise ValueError(f"Unexpected data format: {type(data)}")
        
        for table_name, table_content in tables.items():
            # Check if already in nested dict format (not a list)
            if isinstance(table_content, dict) and not isinstance(list(table_content.values())[0] if table_content else None, list):
                # Already nested dict format: {"user_id": {...}, "user_id2": {...}}
                # But may still need language field selection for nested JSON strings
                processed_table = {}
                for entity_id, entity_data in table_content.items():
                    if isinstance(entity_data, dict):
                        processed_entity = {}
                        # Collect base field names
                        base_fields = set()
                        for key in entity_data.keys():
                            if "." in key:
                                base_field = key.split(".")[0]
                                base_fields.add(base_field)
                            else:
                                base_fields.add(key)
                        
                        # Select appropriate value for each field
                        for field_name in base_fields:
                            value = TranslatedDBLoader.select_language_field(entity_data, field_name, language)
                            if value is not None:
                                # Ensure ID fields are strings
                                if field_name in ["user_id", "flight_id", "flight_number", "reservation_id", "id"]:
                                    value = str(value)
                                processed_entity[field_name] = value
                        
                        processed_table[entity_id] = processed_entity
                    else:
                        processed_table[entity_id] = entity_data
                
                result[table_name] = processed_table
                continue
            
            if not isinstance(table_content, list):
                # Not a table, keep as-is
                result[table_name] = table_content
                continue
            
            # Convert array to dict keyed by _row_key
            table_dict = {}
            for row in table_content:
                if not isinstance(row, dict):
                    continue
                
                # Get the entity ID from _row_key
                entity_id = row.get("_row_key")
                if not entity_id:
                    # Try to infer ID from common fields
                    for id_field in ["user_id", "flight_id", "flight_number", "reservation_id", "id"]:
                        if id_field in row:
                            entity_id = row[id_field]
                            break
                
                if not entity_id:
                    continue
                
                # Build the entity dict with language-specific fields
                entity = {}
                
                # Collect base field names (without language suffix)
                base_fields = set()
                for key in row.keys():
                    if key == "_row_key":
                        continue
                    if "." in key:
                        # Language-specific field like "name.Thai"
                        base_field = key.split(".")[0]
                        base_fields.add(base_field)
                    else:
                        base_fields.add(key)
                
                # Select appropriate value for each field
                for field_name in base_fields:
                    value = TranslatedDBLoader.select_language_field(row, field_name, language)
                    if value is not None:
                        # Ensure ID fields are strings
                        if field_name in ["user_id", "flight_id", "flight_number", "reservation_id", "id"]:
                            value = str(value)
                        entity[field_name] = value
                
                table_dict[str(entity_id)] = entity
            
            result[table_name] = table_dict
        
        return result


class DB(BaseModelNoExtra):
    """Domain database.

    This is a base class for all domain databases.
    """

    @classmethod
    def load(cls, path: str, language: Optional[str] = None) -> "DB":
        """Load the database from a structured file like JSON, YAML, or TOML.
        
        Args:
            path: Path to the database file
            language: Optional language for selecting translated fields (e.g., 'Thai', 'Chinese')
            
        Returns:
            Loaded and validated database instance
        """
        data = load_file(path)
        
        # Check if data is in flat array format and convert if needed
        if TranslatedDBLoader.is_flat_array_format(data):
            data = TranslatedDBLoader.convert_flat_to_nested(data, language)
        
        return cls.model_validate(data)

    def dump(self, path: str, exclude_defaults: bool = False, **kwargs: Any) -> None:
        """Dump the database to a file."""
        data = self.model_dump(exclude_defaults=exclude_defaults)
        dump_file(path, data, **kwargs)

    def get_json_schema(self) -> dict[str, Any]:
        """Get the JSON schema of the database."""
        return self.model_json_schema()

    def get_hash(self) -> str:
        """Get the hash of the database."""
        return get_pydantic_hash(self)

    def get_statistics(self) -> dict[str, Any]:
        """Get the statistics of the database."""
        return {}


def get_db_json_schema(db: Optional[DB] = None) -> dict[str, Any]:
    """Get the JSONschema of the database."""
    if db is None:
        return {}
    return db.get_json_schema()
