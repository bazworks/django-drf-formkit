import os
import subprocess
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand, CommandError


def generate_zod_enum(name, values):
    """Generate a Zod enum schema."""
    enum_values = ", ".join([f"z.literal('{val}')" for val in values])
    return f"export const {name}Schema = z.union([{enum_values}]);"


def parse_property_to_zod(name, prop, required_properties=None):
    """Convert an OpenAPI property to a Zod schema property."""

    def get_base_schema():
        if "$ref" in prop:
            referenced_type = prop["$ref"].split("/")[-1]
            return f"{referenced_type}Schema"
        elif "allOf" in prop:
            # Handle allOf references (commonly used for enums)
            for item in prop["allOf"]:
                if "$ref" in item:
                    referenced_type = item["$ref"].split("/")[-1]
                    return f"{referenced_type}Schema"
            return "z.unknown()"
        elif "type" in prop:
            if prop["type"] == "string":
                if "enum" in prop:
                    enum_values = prop["enum"]
                    return f"z.union([{', '.join(f'z.literal(\'{val}\')' for val in enum_values)}])"
                if "format" in prop:
                    if prop["format"] == "date-time":
                        return "z.string().datetime()"
                    elif prop["format"] == "date":
                        return "z.string()"
                    elif prop["format"] == "email":
                        return "z.string().email()"
                    elif prop["format"] == "decimal":
                        return "z.string()"
                return "z.string()"
            elif prop["type"] == "integer":
                return "z.number().int()"
            elif prop["type"] == "boolean":
                return "z.boolean()"
            elif prop["type"] == "array":
                if "items" in prop:
                    item_schema = parse_property_to_zod("", prop["items"])
                    return f"z.array({item_schema})"
                return "z.array(z.unknown())"
            elif prop["type"] == "object":
                if "properties" in prop:
                    # Handle nested objects
                    nested_props = []
                    for p_name, p_schema in prop["properties"].items():
                        nested_props.append(
                            f"{p_name}: {parse_property_to_zod(p_name, p_schema)}"
                        )
                    return f"z.object({{ {', '.join(nested_props)} }})"
                return "z.record(z.string(), z.unknown())"
        return "z.unknown()"

    schema = get_base_schema()

    if prop.get("nullable", False):
        schema += ".nullable()"
    if required_properties is None or name not in required_properties:
        schema += ".optional()"

    return schema


def generate_zod_schema(schema_name, schema):
    """Generate a Zod schema for a specific OpenAPI schema."""
    # Handle enum schemas
    if "enum" in schema:
        return generate_zod_enum(schema_name, schema["enum"])

    if schema.get("type") != "object" or "properties" not in schema:
        return ""

    required_properties = schema.get("required", [])
    lines = [f"export const {schema_name}Schema = z.object({{"]

    for prop_name, prop in schema["properties"].items():
        zod_type = parse_property_to_zod(prop_name, prop, required_properties)
        lines.append(f"  {prop_name}: {zod_type},")

    lines.append("});")

    return "\n".join(lines)


def parse_property_to_ts(prop, name, required_properties=None, parent_name=None):
    """Convert an OpenAPI property to a TypeScript type."""

    def get_base_type():
        if "$ref" in prop:
            return prop["$ref"].split("/")[-1]
        elif "allOf" in prop:
            # Handle allOf references (commonly used for enums in the schema)
            for item in prop["allOf"]:
                if "$ref" in item:
                    return item["$ref"].split("/")[-1]
            return "unknown"
        elif "type" in prop:
            if prop["type"] == "string":
                if "enum" in prop:
                    # For inline enums, use the parent name and property name
                    enum_name = (
                        f"{parent_name}{name.capitalize()}Enum"
                        if parent_name
                        else f"{name.capitalize()}Enum"
                    )
                    return enum_name
                if "format" in prop:
                    if prop["format"] == "date-time" or prop["format"] == "date":
                        return "string"
                    elif prop["format"] == "email":
                        return "string"
                    elif prop["format"] == "decimal":
                        return "string"
                return "string"
            elif prop["type"] == "integer":
                return "number"
            elif prop["type"] == "boolean":
                return "boolean"
            elif prop["type"] == "array":
                if "items" in prop:
                    item_prop = prop["items"]
                    item_type = (
                        parse_property_to_ts(item_prop, "", None, parent_name)
                        .split(":", 1)[-1]
                        .strip()
                        .rstrip(";")
                    )
                    return f"Array<{item_type}>"
                return "Array<unknown>"
            elif prop["type"] == "object":
                return "Record<string, unknown>"
        return "unknown"

    base_type = get_base_type()

    if prop.get("nullable", False):
        base_type = f"{base_type} | null"

    is_optional = required_properties is None or name not in required_properties
    if name:
        return f"{name}{'?' if is_optional else ''}: {base_type};"
    return base_type


def generate_ts_enum(name, values, description=None):
    """Generate a TypeScript enum with description."""
    lines = []
    if description:
        lines.extend(
            [
                "/**",
                f" * {description}",
                " */",
            ]
        )

    lines.append(f"export enum {name} {{")
    for value in values:
        enum_key = value.upper().replace("-", "_").replace(" ", "_")
        lines.append(f"  {enum_key} = '{value}',")
    lines.append("}")
    return "\n".join(lines)


def generate_ts_interface(name, schema):
    """Generate a TypeScript interface for a specific OpenAPI schema."""
    # Handle enum schemas
    if "enum" in schema:
        return generate_ts_enum(name, schema["enum"], schema.get("description", ""))

    if schema.get("type") != "object" or "properties" not in schema:
        return ""

    # Generate interface
    required_properties = schema.get("required", [])
    lines = []

    # Add description if available
    if "description" in schema:
        lines.extend(
            [
                "/**",
                f" * {schema['description']}",
                " */",
            ]
        )

    lines.append(f"export interface {name} {{")

    for prop_name, prop in schema["properties"].items():
        # Add property description if available
        if "description" in prop:
            lines.extend(
                [
                    "  /**",
                    f"   * {prop['description']}",
                    "   */",
                ]
            )
        ts_type = parse_property_to_ts(prop, prop_name, required_properties, name)
        lines.append(f"  {ts_type}")

    lines.append("}")
    return "\n".join(lines)


def get_schema_dependencies(schema_name, schema, components):
    """Get all schema dependencies for a given schema."""
    deps = set()

    def collect_deps(prop):
        if "$ref" in prop:
            dep = prop["$ref"].split("/")[-1]
            if dep in components:
                deps.add(dep)
        elif "allOf" in prop:
            for item in prop["allOf"]:
                collect_deps(item)
        elif "type" in prop and prop["type"] == "object" and "properties" in prop:
            for p in prop["properties"].values():
                collect_deps(p)
        elif "type" in prop and prop["type"] == "array" and "items" in prop:
            collect_deps(prop["items"])

    if "properties" in schema:
        for prop in schema["properties"].values():
            collect_deps(prop)

    return deps


def sort_schemas(components):
    """Sort schemas based on their dependencies."""
    # Create dependency graph
    graph = {
        name: get_schema_dependencies(name, schema, components)
        for name, schema in components.items()
    }

    # Topological sort
    sorted_names = []
    visited = set()
    temp_visited = set()

    def visit(name):
        if name in temp_visited:
            raise ValueError(f"Circular dependency detected: {name}")
        if name not in visited:
            temp_visited.add(name)
            for dep in graph[name]:
                visit(dep)
            temp_visited.remove(name)
            visited.add(name)
            sorted_names.append(name)

    # Sort schemas
    for name in graph:
        if name not in visited:
            visit(name)

    return sorted_names


class Command(BaseCommand):
    help = "Generate TypeScript interfaces and Zod schemas from an OpenAPI YAML file."

    def add_arguments(self, parser):
        parser.add_argument(
            "output_folder",
            type=str,
            help="Path to the output folder where files will be created.",
        )
        parser.add_argument(
            "--schema_path",
            type=str,
            default="schema.yml",
            help="Path to the generated OpenAPI YAML schema file (default: schema.yml).",
        )

    def handle(self, *args, **options):
        output_folder = options["output_folder"]
        schema_path = options["schema_path"]

        # Ensure the output folder exists
        os.makedirs(output_folder, exist_ok=True)

        # Generate the OpenAPI schema file using `spectacular`
        self.stdout.write("Generating OpenAPI schema YAML file...")
        try:
            subprocess.run(
                ["python", "manage.py", "spectacular", "--file", schema_path],
                check=True,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Schema file generated at {schema_path}")
            )
        except subprocess.CalledProcessError as e:
            raise CommandError("Error while generating schema file.") from e

        # Parse the generated schema file
        if not os.path.exists(schema_path):
            raise CommandError(f"Schema file '{schema_path}' not found.")
        with open(schema_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        components = data.get("components", {}).get("schemas", {})
        if not components:
            raise CommandError("No schemas found in the OpenAPI file.")

        try:
            # Sort schemas based on dependencies
            sorted_schema_names = sort_schemas(components)

            # Generate TypeScript interfaces in dependency order
            interfaces = []
            for schema_name in sorted_schema_names:
                ts_interface = generate_ts_interface(
                    schema_name, components[schema_name]
                )
                if ts_interface:
                    interfaces.append(ts_interface)

            interfaces_output_path = Path(output_folder) / "api_interfaces.ts"
            with open(interfaces_output_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(interfaces))

            self.stdout.write(
                self.style.SUCCESS(
                    f"TypeScript interfaces written to {interfaces_output_path}"
                )
            )

            # Generate Zod schemas in dependency order
            zod_schemas = ["import { z } from 'zod';"]
            for schema_name in sorted_schema_names:
                zod_schema = generate_zod_schema(schema_name, components[schema_name])
                if zod_schema:
                    zod_schemas.append(zod_schema)

            zod_schemas_output_path = Path(output_folder) / "zod_schemas.ts"
            with open(zod_schemas_output_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(zod_schemas))

            self.stdout.write(
                self.style.SUCCESS(f"Zod schemas written to {zod_schemas_output_path}")
            )

        except ValueError as e:
            raise CommandError(f"Error generating schemas: {str(e)}") from e
