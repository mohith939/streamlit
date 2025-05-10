"""
JSON output formatting functionality.
"""
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

class Formatter:
    """
    Formatter for JSON output.
    """

    def __init__(self):
        """
        Initialize the formatter.
        """
        pass

    def format_modules(self, modules):
        """
        Format modules into a structured JSON format.

        Args:
            modules (list): List of module dictionaries

        Returns:
            list: Formatted list of module dictionaries
        """
        formatted_modules = []

        for module in modules:
            formatted_module = {
                "module": module.get("module", ""),
                "Description": module.get("Description", ""),
                "Submodules": module.get("Submodules", {})
            }

            # Clean up empty descriptions
            if not formatted_module["Description"]:
                formatted_module["Description"] = "No description available"

            # Clean up submodules
            cleaned_submodules = {}
            for submodule_name, submodule_desc in formatted_module["Submodules"].items():
                if not submodule_desc:
                    submodule_desc = "No description available"
                cleaned_submodules[submodule_name] = submodule_desc

            formatted_module["Submodules"] = cleaned_submodules

            formatted_modules.append(formatted_module)

        return formatted_modules

    def to_json(self, modules, indent=1):
        """
        Convert modules to JSON string in the exact format required.

        Args:
            modules (list): List of module dictionaries
            indent (int): Indentation level for JSON formatting

        Returns:
            str: JSON string in the required format
        """
        try:
            formatted_modules = self.format_modules(modules)

            # For standard JSON compatibility, we'll use a list of modules
            return json.dumps(formatted_modules, indent=indent)

        except Exception as e:
            logger.error(f"Error converting to JSON: {e}")
            return "[]"

    def to_custom_format(self, modules, indent=1):
        """
        Convert modules to a custom format string that matches the exact format required.
        Note: This is not standard JSON and cannot be parsed with json.loads().

        Args:
            modules (list): List of module dictionaries
            indent (int): Indentation level for JSON formatting

        Returns:
            str: Custom formatted string in the required format
        """
        try:
            formatted_modules = self.format_modules(modules)

            # Create the exact format needed with opening and closing braces
            json_str = "{\n"

            # Add each module
            for i, module in enumerate(formatted_modules):
                module_json = json.dumps(module, indent=indent)

                # Format the module JSON to match the required format
                # Replace the opening and closing braces with the required format
                module_json = " {\n" + "\n".join(module_json.split("\n")[1:-1]) + "\n }"

                # Add comma if not the last module
                if i < len(formatted_modules) - 1:
                    module_json += ","

                json_str += module_json + "\n"

            # Close the JSON string
            json_str += "}"

            return json_str

        except Exception as e:
            logger.error(f"Error converting to custom format: {e}")
            return "{}"

    def to_dict(self, modules):
        """
        Convert modules to Python dictionary.

        Args:
            modules (list): List of module dictionaries

        Returns:
            list: List of formatted module dictionaries
        """
        try:
            return self.format_modules(modules)
        except Exception as e:
            logger.error(f"Error converting to dictionary: {e}")
            return []
