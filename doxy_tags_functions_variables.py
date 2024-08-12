import os
import re

# Define the extensions of the source code files you want to process
SUPPORTED_EXTENSIONS = ('.cpp', '.hpp', '.h', '.c')  # Add more as needed

# Define the Doxygen templates
FUNCTION_TEMPLATE = """
/**
 * @brief Brief description of the function.
 *
 * Detailed description of the function.
 *
 * @param[in] {params}
 * @return Description of the return value.
 */
"""

VARIABLE_TEMPLATE = """
/**
 * @brief Brief description of the variable.
 *
 * Detailed description of the variable.
 */
"""

CLASS_TEMPLATE = """
/**
 * @brief Brief description of the class.
 *
 * Detailed description of the class.
 */
"""

def is_code_complete(line):
    """Check if a line of code is likely to be complete."""
    # Check for semicolon at the end or if it's a one-liner with curly braces
    return line.strip().endswith(';') or '{' in line or '}' in line

def is_valid_function_declaration(match):
    """Validate function declarations to avoid matching code snippets."""
    before_function = match.string[:match.start()].strip()
    # Check that the match is not preceded by characters like '=', '{', or ',' to avoid assignments or initializations.
    if before_function.endswith(('=', '{', ',', ':')):
        return False
    return True

def add_doxygen_to_file(file_path):
    """
    Fucntion that parses the source code file, and adds the doxygen tags to the functions and variables.

    :param file_path: path of the source code files to be modified.
    """    
    with open(file_path, 'r') as file:
        content = file.read()

    # Add Doxygen comments for functions
    function_pattern = re.compile(r'^\s*(\w[\w\s\*&:<>,]*)\s+(\w+)\s*\(([^)]*)\)\s*(const)?\s*{?', re.MULTILINE)
    matches = list(function_pattern.finditer(content))
    if matches:
        for match in reversed(matches):
            if not is_valid_function_declaration(match):
                continue
            return_type, function_name, params, const = match.groups()
            params = ', '.join([param.split()[-1] for param in params.split(',') if param])
            doxygen_comment = FUNCTION_TEMPLATE.format(params=params)
            content = content[:match.start()] + doxygen_comment + content[match.start():]

    # Add Doxygen comments for variables
    variable_pattern = re.compile(r'^\s*(\w[\w\s\*&:<>,]*)\s+(\w+)\s*(=\s*[^;]+)?\s*;', re.MULTILINE)
    matches = list(variable_pattern.finditer(content))
    if matches:
        for match in reversed(matches):
            line_start = content[:match.start()].strip().splitlines()[-1]
            if not is_code_complete(line_start):
                continue  # Skip if the line is likely incomplete
            doxygen_comment = VARIABLE_TEMPLATE
            content = content[:match.start()] + doxygen_comment + content[match.start():]

    # Add Doxygen comments for classes
    class_pattern = re.compile(r'^\s*class\s+(\w+)', re.MULTILINE)
    matches = list(class_pattern.finditer(content))
    if matches:
        for match in reversed(matches):
            doxygen_comment = CLASS_TEMPLATE
            content = content[:match.start()] + doxygen_comment + content[match.start():]

    with open(file_path, 'w') as file:
        file.write(content)

def process_directory(directory):
    """
    Function to process the project directories.

    :param directory: directory to be processed on the way to analyse the right files for modification.
    """  
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(SUPPORTED_EXTENSIONS):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                add_doxygen_to_file(file_path)

if __name__ == "__main__":
    # Set the root directory of the source code project
    root_directory = "path to project" 
    process_directory(root_directory)
