"""
Schema definitions for API requests and responses.
These schemas define the expected structure of the JSON data.
"""

# Request schema for creating an estimate
ESTIMATE_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["square_footage", "bedroom_count"],
    "properties": {
        "square_footage": {"type": "number", "minimum": 1},
        "tier": {"type": "string", "enum": ["Premium", "Luxury", "Ultra-Luxury"]},
        "bedroom_count": {"type": "integer", "minimum": 1},
        "primary_bath_count": {"type": "integer", "minimum": 0},
        "secondary_bath_count": {"type": "integer", "minimum": 0},
        "powder_room_count": {"type": "integer", "minimum": 0},
        "additional_parameters": {"type": "object"}
    }
}

# This file can be expanded with more schemas as the API grows,
# or we could use a library like Marshmallow or Pydantic for more
# sophisticated schema validation and serialization.