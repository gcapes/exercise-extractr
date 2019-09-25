"""
Extract challenges from markdown files.

Usage:
python get_exercises.py markdown_file_or_files output_file
"""

import sys
import os

def extract_exercise(content, end_line):
    """
    Extract challenge block in content, where the last line of the challenge is end_line.
    """
    line_num = end_line - 1
    line = content[line_num]
    exercise_text = []
    prefix = ">"
    while line.startswith(prefix):
        line = line[len(prefix):]
        line = line.strip()

        # Don't extract solutions
        if not line.startswith(prefix) and not line == "{: .solution}":
            exercise_text.insert(0, line)
            line_num = line_num - 1
            line = content[line_num]

    return exercise_text


def check_input_arguments():
    """
    Check script is called with enough arguments.
    :return:
    """
    n_arguments = len(sys.argv)
    assert n_arguments >= 3, "Script requires at least two arguments."


check_input_arguments()

last_input_file = len(sys.argv) - 1
input_files = sys.argv[1:last_input_file]
output_file = sys.argv[-1]

# Delete output file if it already exists - we're appending to it later
if os.path.exists(output_file) and os.path.isfile(output_file):
    os.remove(output_file)

for file in input_files:
    file_name = os.path.basename(file)
    episode_title = "# " + file_name.strip('.md')

    with open(file) as f:
        content = f.readlines()

    # Go through content, looking for exercise markup
    ex_markup = "{: .challenge}"
    exercise_text = []
    for line_num, line in enumerate(content):
        if line.startswith(ex_markup):
            exercise_text.append(extract_exercise(content, line_num))

    # Write exercises to file
    with open(output_file, 'a') as f:
        f.write("%s\n" % episode_title)
        for exercise in exercise_text:
            for line in exercise:
                f.write("%s\n" % line)
            # Separate each exercise with an empty line
            f.write('\n')
