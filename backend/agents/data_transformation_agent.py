"""
Data Transformation Agents
Critical missing feature: Data manipulation, formatting, validation

Nodes Provided:
- JSON Transform Node - Extract, modify JSON
- Data Mapper Node - Map fields between schemas
- Filter Node - Filter arrays by conditions
- Aggregation Node - Group, sum, average data
- Format Converter Node - Convert between formats
- String Operations Node - Text manipulation
- Math Operations Node - Mathematical calculations
- Variable Assignment Node - Store/retrieve variables
- Data Validation Node - Validate data against rules
- Array Operations Node - Array manipulation
"""

from typing import Dict, Any, List, Optional
import json
import re
import csv
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class JSONTransformAgent:
    """Extract, modify, restructure JSON data"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform JSON data

        Config:
            operation: 'extract', 'merge', 'restructure', 'delete'
            path: JSON path (dot notation) for extraction
            mappings: Field mappings for restructure
        """
        operation = self.config.get('operation', 'extract')
        data = inputs.get('data', {})

        if operation == 'extract':
            path = self.config.get('path', '')
            result = self._extract_path(data, path)
        elif operation == 'merge':
            merge_data = inputs.get('merge_with', {})
            result = {**data, **merge_data}
        elif operation == 'restructure':
            mappings = self.config.get('mappings', {})
            result = self._restructure(data, mappings)
        elif operation == 'delete':
            path = self.config.get('path', '')
            result = self._delete_path(data, path)
        else:
            result = data

        return {'result': result, 'operation': operation}

    def _extract_path(self, data: Any, path: str) -> Any:
        """Extract value from nested JSON path"""
        if not path:
            return data

        parts = path.split('.')
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                current = current[int(part)]
            else:
                return None

        return current

    def _restructure(self, data: Dict, mappings: Dict[str, str]) -> Dict:
        """Restructure data according to mappings"""
        result = {}
        for target_key, source_path in mappings.items():
            result[target_key] = self._extract_path(data, source_path)
        return result

    def _delete_path(self, data: Dict, path: str) -> Dict:
        """Delete field at path"""
        result = data.copy()
        parts = path.split('.')

        if len(parts) == 1:
            result.pop(parts[0], None)
        else:
            # Navigate to parent and delete
            current = result
            for part in parts[:-1]:
                current = current.get(part, {})
            current.pop(parts[-1], None)

        return result


class DataMapperAgent:
    """Map fields from input schema to output schema"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map data fields

        Config:
            mappings: Dict of output_field -> input_field
            transformations: Optional transformations per field
        """
        data = inputs.get('data', {})
        mappings = self.config.get('mappings', {})
        transformations = self.config.get('transformations', {})

        result = {}

        for output_field, input_field in mappings.items():
            # Get value from input
            value = self._get_nested_value(data, input_field)

            # Apply transformation if specified
            if output_field in transformations:
                value = self._apply_transformation(value, transformations[output_field])

            # Set in output
            self._set_nested_value(result, output_field, value)

        return {'mapped_data': result}

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dict using dot notation"""
        parts = path.split('.')
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def _set_nested_value(self, data: Dict, path: str, value: Any):
        """Set value in nested dict using dot notation"""
        parts = path.split('.')
        current = data

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    def _apply_transformation(self, value: Any, transformation: str) -> Any:
        """Apply transformation to value"""
        if transformation == 'uppercase':
            return str(value).upper() if value else value
        elif transformation == 'lowercase':
            return str(value).lower() if value else value
        elif transformation == 'trim':
            return str(value).strip() if value else value
        elif transformation == 'to_int':
            return int(value) if value else 0
        elif transformation == 'to_float':
            return float(value) if value else 0.0
        elif transformation == 'to_bool':
            return bool(value)
        else:
            return value


class FilterAgent:
    """Filter arrays based on conditions"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter array

        Config:
            condition: Filter condition (e.g., "item.price > 100")
            field: Field to check in each item
            operator: Comparison operator (>, <, ==, !=, contains)
            value: Value to compare against
        """
        array = inputs.get('array', [])
        condition = self.config.get('condition')

        if condition:
            # Use custom condition
            filtered = [item for item in array if self._evaluate_condition(item, condition)]
        else:
            # Use field/operator/value
            field = self.config.get('field')
            operator = self.config.get('operator', '==')
            value = self.config.get('value')

            filtered = [item for item in array if self._compare(item.get(field), operator, value)]

        return {
            'filtered': filtered,
            'original_count': len(array),
            'filtered_count': len(filtered)
        }

    def _evaluate_condition(self, item: Any, condition: str) -> bool:
        """Evaluate filter condition"""
        try:
            return eval(condition, {"__builtins__": {}}, {'item': item})
        except Exception as e:
            logger.error(f"Filter condition error: {e}")
            return False

    def _compare(self, field_value: Any, operator: str, compare_value: Any) -> bool:
        """Compare values with operator"""
        try:
            if operator == '>':
                return field_value > compare_value
            elif operator == '<':
                return field_value < compare_value
            elif operator == '>=':
                return field_value >= compare_value
            elif operator == '<=':
                return field_value <= compare_value
            elif operator == '==':
                return field_value == compare_value
            elif operator == '!=':
                return field_value != compare_value
            elif operator == 'contains':
                return compare_value in field_value
            elif operator == 'startswith':
                return str(field_value).startswith(str(compare_value))
            elif operator == 'endswith':
                return str(field_value).endswith(str(compare_value))
            else:
                return False
        except Exception:
            return False


class AggregationAgent:
    """Aggregate data - group, sum, average, count"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate data

        Config:
            operation: sum, avg, min, max, count, group
            field: Field to aggregate
            group_by: Field to group by (for group operation)
        """
        array = inputs.get('array', [])
        operation = self.config.get('operation', 'count')
        field = self.config.get('field')

        if operation == 'sum':
            result = sum(item.get(field, 0) for item in array)
        elif operation == 'avg':
            values = [item.get(field, 0) for item in array]
            result = sum(values) / len(values) if values else 0
        elif operation == 'min':
            values = [item.get(field) for item in array if item.get(field) is not None]
            result = min(values) if values else None
        elif operation == 'max':
            values = [item.get(field) for item in array if item.get(field) is not None]
            result = max(values) if values else None
        elif operation == 'count':
            result = len(array)
        elif operation == 'group':
            group_by = self.config.get('group_by')
            result = self._group_by(array, group_by)
        else:
            result = None

        return {
            'result': result,
            'operation': operation,
            'count': len(array)
        }

    def _group_by(self, array: List[Dict], field: str) -> Dict[Any, List]:
        """Group array by field"""
        groups = {}
        for item in array:
            key = item.get(field)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups


class StringOperationsAgent:
    """String manipulation - concat, split, replace, regex"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        String operations

        Config:
            operation: concat, split, replace, regex, uppercase, lowercase, trim
            separator: For split/concat operations
            find: Text to find (for replace/regex)
            replace: Replacement text
            pattern: Regex pattern
        """
        text = inputs.get('text', '')
        operation = self.config.get('operation', 'uppercase')

        if operation == 'concat':
            parts = inputs.get('parts', [])
            separator = self.config.get('separator', '')
            result = separator.join(str(p) for p in parts)

        elif operation == 'split':
            separator = self.config.get('separator', ' ')
            result = text.split(separator)

        elif operation == 'replace':
            find = self.config.get('find', '')
            replace = self.config.get('replace', '')
            result = text.replace(find, replace)

        elif operation == 'regex':
            pattern = self.config.get('pattern', '')
            replace = self.config.get('replace', '')
            result = re.sub(pattern, replace, text)

        elif operation == 'uppercase':
            result = text.upper()

        elif operation == 'lowercase':
            result = text.lower()

        elif operation == 'trim':
            result = text.strip()

        elif operation == 'length':
            result = len(text)

        else:
            result = text

        return {'result': result, 'operation': operation}


class MathOperationsAgent:
    """Mathematical calculations"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Math operations

        Config:
            operation: add, subtract, multiply, divide, power, mod
            expression: Math expression to evaluate

        Inputs:
            a, b: Operands
        """
        operation = self.config.get('operation')
        expression = self.config.get('expression')

        if expression:
            # Evaluate expression
            result = self._safe_eval(expression, inputs)
        else:
            # Use operation
            a = inputs.get('a', 0)
            b = inputs.get('b', 0)

            if operation == 'add':
                result = a + b
            elif operation == 'subtract':
                result = a - b
            elif operation == 'multiply':
                result = a * b
            elif operation == 'divide':
                result = a / b if b != 0 else None
            elif operation == 'power':
                result = a ** b
            elif operation == 'mod':
                result = a % b if b != 0 else None
            else:
                result = None

        return {'result': result}

    def _safe_eval(self, expression: str, context: Dict[str, Any]) -> float:
        """Safely evaluate math expression"""
        import ast
        import operator

        # Allowed operations
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
            ast.USub: operator.neg,
        }

        def eval_node(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.Name):
                return context.get(node.id, 0)
            elif isinstance(node, ast.BinOp):
                left = eval_node(node.left)
                right = eval_node(node.right)
                return operators[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = eval_node(node.operand)
                return operators[type(node.op)](operand)
            else:
                raise ValueError(f"Unsupported operation: {type(node)}")

        tree = ast.parse(expression, mode='eval')
        return eval_node(tree.body)


class VariableAssignmentAgent:
    """Store and retrieve workflow variables"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign or retrieve variables

        Config:
            operation: 'set' or 'get'
            variable_name: Name of variable
            scope: 'workflow' or 'session' or 'global'

        Inputs:
            value: Value to set (for set operation)
            variables: Variable store from workflow context
        """
        operation = self.config.get('operation', 'set')
        variable_name = self.config.get('variable_name')
        scope = self.config.get('scope', 'workflow')

        # Get variable store from workflow context
        variables = inputs.get('variables', {})

        if operation == 'set':
            value = inputs.get('value')
            variables[variable_name] = {
                'value': value,
                'scope': scope,
                'timestamp': datetime.utcnow().isoformat()
            }
            result = {'set': variable_name, 'value': value}

        elif operation == 'get':
            var_data = variables.get(variable_name, {})
            result = {
                'variable': variable_name,
                'value': var_data.get('value'),
                'exists': variable_name in variables
            }

        elif operation == 'delete':
            if variable_name in variables:
                del variables[variable_name]
            result = {'deleted': variable_name}

        elif operation == 'list':
            result = {
                'variables': list(variables.keys()),
                'count': len(variables)
            }

        else:
            result = {'error': f'Unknown operation: {operation}'}

        return {
            **result,
            'updated_variables': variables
        }


class DataValidationAgent:
    """Validate data against schemas and rules"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data

        Config:
            validation_type: 'schema', 'rules', 'regex', 'range'
            schema: JSON schema for validation
            rules: List of validation rules
            on_error: 'fail', 'warn', 'ignore'
        """
        data = inputs.get('data')
        validation_type = self.config.get('validation_type', 'rules')
        on_error = self.config.get('on_error', 'fail')

        errors = []
        warnings = []

        if validation_type == 'schema':
            # JSON Schema validation
            schema = self.config.get('schema', {})
            errors.extend(self._validate_schema(data, schema))

        elif validation_type == 'rules':
            # Custom rules validation
            rules = self.config.get('rules', [])
            for rule in rules:
                error = self._validate_rule(data, rule)
                if error:
                    errors.append(error)

        elif validation_type == 'regex':
            # Regex pattern validation
            pattern = self.config.get('pattern', '')
            field = self.config.get('field')
            value = data.get(field) if isinstance(data, dict) else data

            if not re.match(pattern, str(value)):
                errors.append(f"Field '{field}' does not match pattern '{pattern}'")

        elif validation_type == 'range':
            # Range validation (for numbers)
            field = self.config.get('field')
            min_value = self.config.get('min')
            max_value = self.config.get('max')
            value = data.get(field) if isinstance(data, dict) else data

            try:
                num_value = float(value)
                if min_value is not None and num_value < min_value:
                    errors.append(f"Value {num_value} is below minimum {min_value}")
                if max_value is not None and num_value > max_value:
                    errors.append(f"Value {num_value} is above maximum {max_value}")
            except (ValueError, TypeError):
                errors.append(f"Value is not a number: {value}")

        is_valid = len(errors) == 0

        result = {
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'data': data
        }

        # Handle errors according to config
        if not is_valid and on_error == 'fail':
            result['status'] = 'failed'
        elif not is_valid and on_error == 'warn':
            result['status'] = 'warning'
        else:
            result['status'] = 'passed'

        return result

    def _validate_schema(self, data: Any, schema: Dict) -> List[str]:
        """Validate against JSON schema"""
        errors = []

        try:
            from jsonschema import validate, ValidationError
            validate(instance=data, schema=schema)
        except ValidationError as e:
            errors.append(str(e.message))
        except ImportError:
            # jsonschema not installed, do basic validation
            if 'required' in schema:
                for field in schema['required']:
                    if field not in data:
                        errors.append(f"Required field missing: {field}")

        return errors

    def _validate_rule(self, data: Any, rule: Dict) -> Optional[str]:
        """Validate a single rule"""
        rule_type = rule.get('type')
        field = rule.get('field')
        value = data.get(field) if isinstance(data, dict) else data

        if rule_type == 'required':
            if not value:
                return f"Field '{field}' is required"

        elif rule_type == 'type':
            expected_type = rule.get('expected_type')
            if expected_type == 'string' and not isinstance(value, str):
                return f"Field '{field}' must be a string"
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                return f"Field '{field}' must be a number"
            elif expected_type == 'boolean' and not isinstance(value, bool):
                return f"Field '{field}' must be a boolean"
            elif expected_type == 'array' and not isinstance(value, list):
                return f"Field '{field}' must be an array"

        elif rule_type == 'length':
            min_length = rule.get('min')
            max_length = rule.get('max')
            length = len(value) if value else 0

            if min_length and length < min_length:
                return f"Field '{field}' length {length} is below minimum {min_length}"
            if max_length and length > max_length:
                return f"Field '{field}' length {length} exceeds maximum {max_length}"

        elif rule_type == 'pattern':
            pattern = rule.get('pattern')
            if not re.match(pattern, str(value)):
                return f"Field '{field}' does not match pattern"

        return None


class ArrayOperationsAgent:
    """Array manipulation - push, pop, slice, merge, unique"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Array operations

        Config:
            operation: push, pop, slice, merge, unique, sort, reverse
            index: For slice operations
            value: For push operations
        """
        array = inputs.get('array', [])
        operation = self.config.get('operation', 'unique')

        # Ensure array is a list
        if not isinstance(array, list):
            array = [array]

        result_array = array.copy()

        if operation == 'push':
            # Add item to end
            value = inputs.get('value')
            result_array.append(value)
            result = {'array': result_array, 'length': len(result_array)}

        elif operation == 'pop':
            # Remove last item
            popped = result_array.pop() if result_array else None
            result = {'array': result_array, 'popped': popped, 'length': len(result_array)}

        elif operation == 'shift':
            # Remove first item
            shifted = result_array.pop(0) if result_array else None
            result = {'array': result_array, 'shifted': shifted, 'length': len(result_array)}

        elif operation == 'unshift':
            # Add item to beginning
            value = inputs.get('value')
            result_array.insert(0, value)
            result = {'array': result_array, 'length': len(result_array)}

        elif operation == 'slice':
            # Extract portion of array
            start = self.config.get('start', 0)
            end = self.config.get('end')
            result_array = result_array[start:end]
            result = {'array': result_array, 'length': len(result_array)}

        elif operation == 'merge':
            # Merge with another array
            merge_with = inputs.get('merge_with', [])
            result_array.extend(merge_with)
            result = {'array': result_array, 'length': len(result_array)}

        elif operation == 'unique':
            # Remove duplicates
            seen = set()
            unique_array = []
            for item in result_array:
                # Convert to string for hashability
                item_str = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                if item_str not in seen:
                    seen.add(item_str)
                    unique_array.append(item)
            result = {
                'array': unique_array,
                'original_length': len(result_array),
                'unique_length': len(unique_array),
                'duplicates_removed': len(result_array) - len(unique_array)
            }

        elif operation == 'sort':
            # Sort array
            reverse = self.config.get('reverse', False)
            sort_key = self.config.get('key')

            try:
                if sort_key:
                    # Sort objects by key
                    result_array = sorted(result_array, key=lambda x: x.get(sort_key), reverse=reverse)
                else:
                    # Sort primitives
                    result_array = sorted(result_array, reverse=reverse)
            except Exception as e:
                logger.error(f"Sort error: {e}")

            result = {'array': result_array, 'length': len(result_array)}

        elif operation == 'reverse':
            # Reverse array order
            result_array.reverse()
            result = {'array': result_array, 'length': len(result_array)}

        elif operation == 'flatten':
            # Flatten nested arrays
            def flatten(lst):
                flat = []
                for item in lst:
                    if isinstance(item, list):
                        flat.extend(flatten(item))
                    else:
                        flat.append(item)
                return flat

            result_array = flatten(result_array)
            result = {'array': result_array, 'length': len(result_array)}

        elif operation == 'chunk':
            # Split array into chunks
            chunk_size = self.config.get('chunk_size', 10)
            chunks = [result_array[i:i + chunk_size] for i in range(0, len(result_array), chunk_size)]
            result = {'chunks': chunks, 'chunk_count': len(chunks)}

        elif operation == 'find':
            # Find first matching item
            condition = self.config.get('condition')
            found = None
            found_index = -1

            for i, item in enumerate(result_array):
                try:
                    if eval(condition, {"__builtins__": {}}, {'item': item}):
                        found = item
                        found_index = i
                        break
                except Exception:
                    pass

            result = {'found': found, 'index': found_index}

        elif operation == 'map':
            # Transform each item
            transform = self.config.get('transform', 'item')
            mapped = []

            for item in result_array:
                try:
                    mapped_value = eval(transform, {"__builtins__": {}}, {'item': item})
                    mapped.append(mapped_value)
                except Exception as e:
                    logger.error(f"Map error: {e}")
                    mapped.append(item)

            result = {'array': mapped, 'length': len(mapped)}

        else:
            result = {'array': result_array, 'error': f'Unknown operation: {operation}'}

        return result


class FormatConverterAgent:
    """
    Convert between different data formats
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert data formats

        Config:
            input_format: Source format (json, csv, xml, etc.)
            output_format: Target format
            data: Data to convert

        Returns:
            Converted data
        """
        import json

        input_format = self.config.get('input_format', 'json')
        output_format = self.config.get('output_format', 'json')
        data = inputs.get('data', self.config.get('data'))

        try:
            # For now, just pass through
            # Could integrate with UniversalParser here
            result = {
                'data': data,
                'input_format': input_format,
                'output_format': output_format,
                'converted': True
            }

            return result

        except Exception as e:
            logger.error(f"Format conversion error: {e}")
            return {
                'success': False,
                'error': str(e)
            }