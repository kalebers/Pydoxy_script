import os
import re
from typing import List, Tuple
from enum import Enum, auto

# Define the extensions of the source code files you want to process
SUPPORTED_EXTENSIONS: Tuple[str, ...] = ('.cpp', '.hpp', '.h', '.c')  # Add more as needed

class VariableType(Enum):
    CONSTANT = auto()
    POINTER_OR_REFERENCE = auto()
    ARRAY = auto()
    VARIABLE = auto()

# Define the Doxygen templates
FUNCTION_TEMPLATE: str = """
// StateDiagramRef: Instruction TODO
/**
 * @brief {brief_description}
 *
 * {detailed_description}
 *
 * @param[in] {params}
 * @return {return_description}
 */
"""

VARIABLE_TEMPLATE: str = """
// StateDiagramNaming: Variable Definition TODO
/**
 * @brief {brief_description}
 *
 * {detailed_description}
 */
"""

STRUCT_TEMPLATE: str = """
// StateDiagramRef: Instruction TODO
/**
 * @brief Brief description of the {struct_type} {struct_name}.
 *
 * Detailed description of the {struct_type} {struct_name}.
 */
"""

CONSTANT_TEMPLATE: str = """
// StateDiagramNaming: Constant Definition TODO
/**
 * @brief Constant representing {constant_name}.
 *
 * Detailed description of the constant {constant_name}.
 */
"""

def detect_variable_type(declaration: str) -> VariableType:
    """
    Detects the type of a variable based on its declaration.

    :param declaration: The declaration of the variable.
    :return: An Enum representing the type of the variable.
    """
    if 'const' in declaration:
        return VariableType.CONSTANT
    if '*' in declaration or '&' in declaration:
        return VariableType.POINTER_OR_REFERENCE
    if re.match(r'.*\[\s*\d*\s*\]', declaration):
        return VariableType.ARRAY
    return VariableType.VARIABLE  # Default case

def generate_function_comment(return_type: str, function_name: str, params: str) -> str:
    """
    Generates a Doxygen comment for a function based on its return type, name, and parameters.

    :param return_type: The return type of the function.
    :param function_name: The name of the function.
    :param params: The parameters of the function.
    :return: A string containing the Doxygen comment.
    """
    formatted_params = ', '.join([param.split()[-1] for param in params.split(',') if param])

    brief_description = f"Brief description of the function {function_name}."
    detailed_description = f"Detailed description of the function {function_name}."
    return_description = f"Return value of {function_name}." if return_type.strip() != "void" else "No return value."

    return FUNCTION_TEMPLATE.format(
        brief_description=brief_description,
        detailed_description=detailed_description,
        params=formatted_params,
        return_description=return_description
    )

def generate_variable_comment(var_type: VariableType, variable_name: str) -> str:
    """
    Generates a Doxygen comment for a variable based on its type and name.

    :param var_type: The type of the variable.
    :param variable_name: The name of the variable.
    :return: A string containing the Doxygen comment.
    """
    if var_type == VariableType.CONSTANT:
        return CONSTANT_TEMPLATE.format(constant_name=variable_name)
    
    brief_description = f"Brief description of the {var_type.name.lower()} {variable_name}."
    detailed_description = f"Detailed description of the {var_type.name.lower()} {variable_name}."
    
    return VARIABLE_TEMPLATE.format(
        brief_description=brief_description,
        detailed_description=detailed_description
    )

def generate_struct_comment(struct_name: str) -> str:
    """
    Generates a Doxygen comment for a struct based on its name.

    :param struct_name: The name of the struct.
    :return: A string containing the Doxygen comment.
    """
    return STRUCT_TEMPLATE.format(struct_type="struct", struct_name=struct_name)

def is_preceded_by_comment(content: str, start_index: int) -> bool:
    """
    Checks if the code at the given index is preceded by a comment.

    :param content: The content of the file.
    :param start_index: The index at which to check for a preceding comment.
    :return: True if the code is preceded by a comment, otherwise False.
    """
    lines_before = content[:start_index].strip().splitlines()
    if not lines_before:
        return False
    
    previous_line = lines_before[-1].strip()

    if previous_line.startswith('//'):
        return True
    
    # Check for multi-line comment
    if '*/' in previous_line:
        # Search for '/*' in preceding lines
        for line in reversed(lines_before):
            if '/*' in line:
                return True
            if '*/' in line:
                break

    return False

def add_doxygen_to_file(file_path: str) -> None:
    """
    Parses the source code file and adds the Doxygen and PlantUML tags to the functions, variables, and structs.

    :param file_path: Path of the source code file to be modified.
    """    
    with open(file_path, 'r') as file:
        content: str = file.read()

    content = add_doxygen_to_functions(content)
    content = add_doxygen_to_variables(content)
    content = add_doxygen_to_structs(content)

    with open(file_path, 'w') as file:
        file.write(content)

def add_doxygen_to_functions(content: str) -> str:
    """
    Adds Doxygen comments to functions in the content.

    :param content: The content of the file.
    :return: The content with Doxygen comments added for functions.
    """
    function_pattern = re.compile(r'^\s*(\w[\w\s\*&:<>,]*)\s+(\w+)\s*\(([^)]*)\)\s*(const)?\s*{?', re.MULTILINE)
    function_matches: List[re.Match] = list(function_pattern.finditer(content))

    for match in reversed(function_matches):
        return_type, function_name, params, _ = match.groups()

        # Skip adding comment if function is already preceded by a comment
        if is_preceded_by_comment(content, match.start()):
            continue

        doxygen_comment = generate_function_comment(return_type, function_name, params)
        content = content[:match.start()] + doxygen_comment + content[match.start():]

    return content

def add_doxygen_to_variables(content: str) -> str:
    """
    Adds Doxygen comments to variables in the content.

    :param content: The content of the file.
    :return: The content with Doxygen comments added for variables.
    """
    variable_pattern = re.compile(r'^\s*(\w[\w\s\*&:<>,]*)\s+(\w+)\s*(=\s*[^;]+)?\s*;', re.MULTILINE)
    variable_matches: List[re.Match] = list(variable_pattern.finditer(content))

    for match in reversed(variable_matches):
        declaration_type, variable_name, _ = match.groups()

        # Skip adding comment if variable is already preceded by a comment
        if is_preceded_by_comment(content, match.start()):
            continue

        var_type = detect_variable_type(declaration_type)
        doxygen_comment = generate_variable_comment(var_type, variable_name)
        content = content[:match.start()] + doxygen_comment + content[match.start():]

    return content

def add_doxygen_to_structs(content: str) -> str:
    """
    Adds Doxygen comments to structs in the content.

    :param content: The content of the file.
    :return: The content with Doxygen comments added for structs.
    """
    struct_pattern = re.compile(r'^\s*struct\s+(\w+)', re.MULTILINE)
    struct_matches: List[re.Match] = list(struct_pattern.finditer(content))

    for match in reversed(struct_matches):
        struct_name = match.group(1)

        # Skip adding comment if struct is already preceded by a comment
        if is_preceded_by_comment(content, match.start()):
            continue

        doxygen_comment = generate_struct_comment(struct_name)
        content = content[:match.start()] + doxygen_comment + content[match.start():]

    return content

def process_directory(directory: str) -> None:
    """
    Processes the project directories to find and modify source code files.

    :param directory: Directory to be processed to find the relevant files for modification.
    """  
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(SUPPORTED_EXTENSIONS):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                add_doxygen_to_file(file_path)

if __name__ == "__main__":
    # Set the root directory as the current directory
    root_directory: str = "./" 
    process_directory(root_directory)
