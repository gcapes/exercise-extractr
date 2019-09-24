import sys

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
        exercise_text.insert(0, line)
        line_num = line_num - 1
        line = content[line_num]

    return exercise_text


markdown_file = sys.argv[1]
assert markdown_file.endswith('.md')
output_file = sys.argv[2]

with open(markdown_file) as f:
    content = f.readlines()

# Go through content, looking for exercise markup
ex_markup = "{: .challenge}"
exercise_text = []
for line_num, line in enumerate(content):
    if line.startswith(ex_markup):
        exercise_text.append(extract_exercise(content, line_num))

# Write exercises to file
with open(output_file, 'w') as f:
    for exercise in exercise_text:
        for line in exercise:
            f.write("%s\n" % line)
        # Separate each exercise with an empty line
        f.write('\n')


