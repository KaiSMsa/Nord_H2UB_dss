import re

def modify_lp_file(input_file, output_file):
    # Regular expression to match variable names of the format: <name>[<indices>]
    variable_pattern = re.compile(r"(\w+)\[(\d+,\d+(?:,\d+)*)\]")

    with open(input_file, "r") as file:
        lp_content = file.read()

    # Replace variable names
    modified_content = variable_pattern.sub(
        lambda match: f"{match.group(1)}_{match.group(2).replace(',', '_')}",
        lp_content,
    )

    # Write the modified content to the new file
    with open(output_file, "w") as file:
        file.write(modified_content)

# Example usage
input_lp_file = "facility_location_model.lp"
output_lp_file = "facility_location_model_cplex.lp"

modify_lp_file(input_lp_file, output_lp_file)
print(f"Modified LP file written to {output_lp_file}")
