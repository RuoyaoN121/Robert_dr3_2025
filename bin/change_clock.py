import os

# Directory containing the .par files
directory = r'/fred/oz002/users/mbailes/astral/timing2025/GWB_search_2/'  # change this if your files are elsewhere

# Initialize a counter for the number of replacements
total_replacements = 0

print(os.listdir(directory))

# Iterate over all files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.par'):
        file_path = os.path.join(directory, filename)
        
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        changed = False
        for i, line in enumerate(lines):
            if line.strip().startswith('CLK'):
                # Replace the line with the new clock specification
                new_line = 'CLK            TT(BIPM2024)\n'
                lines[i] = new_line
                total_replacements += 1
                changed = True
        
        # If changes were made, rewrite the file
        if changed:
            with open(file_path, 'w') as file:
                file.writelines(lines)

print(f'Total replacements made: {total_replacements}')
