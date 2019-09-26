"""
Extract challenges from markdown files.

Usage:
python get_exercises.py markdown_file_or_files output_file
"""

import sys
import os
import re

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
            links = get_reference_links(content, line)
            if links:
                for link in links:
                    exercise_text.append(link)

            line = subsitute_variable_from_yaml(yaml_config, line)
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
    assert n_arguments >= 4, "Script requires at least three arguments."


def get_reference_links(file_contents, line):
    """
    Get reference-style links
    :param file_contents:
    :param line:
    :return:
    """
    regex = "\[.+\](\[\S+\])"
    matches = re.findall(regex, line)

    if matches:
        links = []
        for reference in matches:
            # Get all links
            for search_line in file_contents:
                if search_line.startswith(reference + ':'):
                    links.append(search_line.strip('\n'))
        return links

    else:
        return None


def move_links_to_end(text):
    """
    Search through contents for reference-style links throughout the text,
    and collect them together at the end of the episode.
    :param contents:
    :return:
    """
    links = []
    for exercise in text:
        for line in exercise:
            if re.search("\[.*\]:.*", line):
                links.append(line)
                exercise.remove(line)

    text.append(links)

    return text


def subsitute_variable_from_yaml(yaml_file, input_line):
    """
    :param input_line: string to parse
    :param yaml: yaml config file for repo
    :return:
    """
    with open(yaml_file) as f:
        yaml = f.readlines()

    var_pattern = "{{(.*)}}"
    matches =  re.findall(var_pattern, input_line)

    for var in matches:
        var = re.sub('site\.',"", var)
        # site.XXX seems to be the same as just XXX
        for line in yaml:
            if line.startswith(var):
                value = line[len(var)+1:]
                value = value.strip('\n')
                value = value.strip()
                value = value.strip('"')
                value = value.strip()

                input_line = re.sub(var_pattern, value, input_line)

    return input_line


check_input_arguments()

yaml_config = sys.argv[1]
last_input_file = len(sys.argv) - 1
input_files = sys.argv[2:last_input_file]
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

    exercise_text = move_links_to_end(exercise_text)

    # Write exercises to file
    with open(output_file, 'a') as f:
        # Only print episode title if there are exercises
        if len(exercise_text) > 1:
            f.write("%s\n" % episode_title)
            for exercise in exercise_text:
                for line in exercise:
                    f.write("%s\n" % line)
                # Separate each exercise with an empty line
                f.write('\n')
