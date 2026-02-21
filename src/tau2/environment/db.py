import json
from typing import Any, Dict, List, Optional

from tau2.utils import dump_file, get_pydantic_hash, load_file
from tau2.utils.pydantic_utils import BaseModelNoExtra


class TranslatedDBLoader:
    """Helper class to load and transform translated database files.
    
    Translated files are flat arrays with:
    - _row_key: the original entity ID
    - Language-suffixed fields: e.g., name.Thai, address.Chinese
    - JSON-encoded nested fields that need parsing
    
    This class transforms them back to the nested dict structure expected by tools.
    """
    
    @staticmethod
    def is_translated_format(data: Any) -> bool:
        """Check if data is in translated flat array format."""
        if not isinstance(data, list) or len(data) == 0:
            return False
        # Check if first item has _row_key field (marker of translated format)
        return isinstance(data[0], dict) and "_row_key" in data[0]
    
    @staticmethod
    def parse_json_field(value: Any) -> Any:
        """Parse JSON-encoded string fields, or return as-is if not a JSON string."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                # Not a JSON string, return as-is
                return value
        return value
    
    @staticmethod
    def get_language_field(row: Dict[str, Any], field_name: str, language: Optional[str]) -> Any:
        """Get the appropriate field value based on language.
        
        Args:
            row: The data row
            field_name: Base field name (e.g., "name")
            language: Target language (e.g., "Thai"), or None for original
            
        Returns:
            The field value, with language preference and JSON parsing applied
        """
        # Try language-specific field first if language is specified
        if language:
            lang_field = f"{field_name}.{language}"
            if lang_field in row:
                value = row[lang_field]
                return TranslatedDBLoader.parse_json_field(value)
        
        # Fall back to original field
        if field_name in row:
            value = row[field_name]
            return TranslatedDBLoader.parse_json_field(value)
        
        return None
    
    @staticmethod
    def normalize_id_fields(entity: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure ID fields are strings, not numbers.
        
        Args:
            entity: Entity dictionary
            
        Returns:
            Entity with normalized ID fields
        """
        # Common ID field patterns that should always be strings
        id_patterns = ['_id', 'id']
        
        for key, value in entity.items():
            # Check if field name suggests it's an ID field
            is_id_field = any(pattern in key.lower() for pattern in id_patterns)
            
            # Convert numeric IDs to strings
            if is_id_field and isinstance(value, (int, float)):
                entity[key] = str(int(value))  # Use int() first to remove .0 from floats
        
        return entity
    
    @staticmethod
    def convert_flat_to_nested(
        data: List[Dict[str, Any]], 
        language: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Convert flat array format to nested dict format.
        
        Args:
            data: Flat array with _row_key and language-suffixed fields
            language: Target language for field selection (e.g., "Thai")
            
        Returns:
            Nested dict: {entity_id: {field1: value1, ...}}
        """
        result = {}
        
        for row in data:
            # Get the entity ID from _row_key
            entity_id = row.get("_row_key")
            if not entity_id:
                continue
            
            # Ensure entity_id is a string
            if isinstance(entity_id, (int, float)):
                entity_id = str(int(entity_id))
            
            # Find all base field names (without language suffixes)
            base_fields = set()
            for key in row.keys():
                if key == "_row_key":
                    continue
                # Strip language suffix if present
                base_field = key.split(".")[0]
                base_fields.add(base_field)
            
            # Build entity dict with language-aware field selection
            entity = {}
            for field_name in base_fields:
                value = TranslatedDBLoader.get_language_field(row, field_name, language)
                if value is not None:
                    entity[field_name] = value
            
            # Normalize ID fields to strings
            entity = TranslatedDBLoader.normalize_id_fields(entity)
            
            result[entity_id] = entity
        
        return result
    
    @staticmethod
    def transform_database(
        data: Any, 
        language: Optional[str] = None
    ) -> Any:
        """Transform database structure based on format.
        
        For translated flat arrays: converts to nested dict per table
        For standard nested dict: returns as-is (or with language selection if implemented)
        
        Args:
            data: Database data (either flat array or nested dict)
            language: Target language
            
        Returns:
            Transformed data in nested dict format
        """
        # Handle nested dict with table names (e.g., {flights: [...], users: [...]})
        if isinstance(data, dict):
            result = {}
            for table_name, table_data in data.items():
                if TranslatedDBLoader.is_translated_format(table_data):
                    # Convert flat array to nested dict
                    result[table_name] = TranslatedDBLoader.convert_flat_to_nested(
                        table_data, language
                    )
                else:
                    # Keep as-is (already nested dict format)
                    result[table_name] = table_data
            return result
        
        # Handle single flat array (entire DB is one table)
        if TranslatedDBLoader.is_translated_format(data):
            return TranslatedDBLoader.convert_flat_to_nested(data, language)
        
        # Return as-is for standard formats
        return data


class DB(BaseModelNoExtra):
    """Domain database.

    This is a base class for all domain databases.
    """

    @classmethod
    def load(cls, path: str, language: Optional[str] = None) -> "DB":
        """Load the database from a structured file like JSON, YAML, or TOML.
        
        Args:
            path: Path to the database file
            language: Optional language for translated databases (e.g., "Thai", "Chinese")
                     If None, loads original/English version
        
        Returns:
            Loaded and validated database instance
        """
        data = load_file(path)
        
        # Transform data if it's in translated format
        if language:
            data = TranslatedDBLoader.transform_database(data, language)
        
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
