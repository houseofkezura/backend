from typing import Dict, Any

def validate_json_data(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Performs basic validation of a JSON data payload against a given schema.
    This is a simplified validator that checks for key presence and basic type matching.
    For robust and comprehensive JSON schema validation in a production environment,
    consider using a dedicated library like 'jsonschema'.

    :param data: The JSON data payload to validate (e.g., {"name": "John", "age": 30}).
    :param schema: The schema definition (e.g., {"name": "string", "age": "integer"}).
                   Supported types in this basic validator: 'string', 'integer', 'boolean', 'number'.
    :return: True if validation passes, False otherwise.
    """
    # Ensure the provided data is a dictionary
    if not isinstance(data, dict):
        return False

    # Check if all required fields in the schema are present in the data
    for key, expected_type_str in schema.items():
        if key not in data:
            # Assuming all fields defined in the schema are required.
            # This logic can be extended to support optional fields if needed.
            return False

        value = data[key] # Get the value from the data payload

        # Validate the type of the value against the expected type in the schema
        if expected_type_str == "string":
            if not isinstance(value, str):
                return False
        elif expected_type_str == "integer":
            if not isinstance(value, int):
                return False
        elif expected_type_str == "boolean":
            if not isinstance(value, bool):
                return False
        elif expected_type_str == "number":
            # 'number' can be either an int or a float
            if not isinstance(value, (int, float)):
                return False
        # Add more type validations here if your schemas use other basic types (e.g., "array", "object")
        else:
            # If an unknown type is encountered in the schema, consider it an invalid schema definition
            # or handle it based on your application's requirements.
            return False
    return True # All checks passed, data is valid according to the schema
