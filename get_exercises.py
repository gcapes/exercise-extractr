"""
Extract challenges from markdown files.

Usage:
python get_exercises.py markdown_file_or_files output_file
"""

import glob
import os
import re
import subprocess
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
        # Check for single-space after prefix
        line_start = len(prefix)
        if line[line_start] == " ":
            line_start += 1
        line = line[line_start:]
        line = line.strip("\n")

        # Don't extract solutions
        if not line.startswith(prefix) and not line == "{: .solution}":
            links = get_reference_links(content, line)
            if links:
                for link in links:
                    exercise_text.append(link)

            line = substitute_variable_from_yaml(yaml_config, line)
            line = substitute_internal_links(line, website_url)
            line = resolve_file_links(line, repo_blob_from_remote(remote_url))
            line = replace_etherpad_with_shared_doc(line)
            exercise_text.insert(0, line)
        line_num = line_num - 1
        line = content[line_num]

    return exercise_text


def check_input_arguments():
    """
    Check script is called with correct arguments.
    :return:
    """
    lesson_dir = sys.argv[1]
    assert os.path.isdir(lesson_dir), "Expected lesson repo directory"


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


def substitute_variable_from_yaml(yaml_file, input_line):
    """
    :param input_line: string to parse
    :param yaml: yaml config file for repo
    :return:
    """
    with open(yaml_file) as f:
        yaml = f.readlines()

    var_pattern = "{{(.*)}}"
    matches = re.findall(var_pattern, input_line)

    for var in matches:
        var = re.sub('(site|page)\.',"", var)
        # site.XXX seems to be the same as just XXX
        var = var.strip()
        for line in yaml:
            if line.startswith(var):
                value = line[len(var)+1:]
                value = value.strip('\n')
                value = value.strip()
                value = value.strip('"')
                value = value.strip()

                input_line = re.sub(var_pattern, value, input_line)

    return input_line

def repo_blob_from_remote(remote_url):
    """
    Get repo blob URL stem for file downloads
    e.g. https://github.com/carpentries/instructor-training/blob/gh-pages/
    :param remote_url:
    :return: URL stem for file downloads
    """
    pattern = r'.*github\.com.([^/]*)/(.*)\.git$'
    match = re.match(pattern, remote_url)
    if match:
        account, lesson = match.groups()
        blob = f"https://github.com/{account}/{lesson}/blob/gh-pages"

    return blob


def github_pages_from_remote(remote_url):
    """
    Get github pages URL from git remote
    :param website_base_url:
    :return:
    """
    pattern = r'.*github\.com.([^/]*)/(.*)\.git$'
    match = re.match(pattern, remote_url)
    if match:
        account, lesson  = match.groups()
        website_base_url = f"https://{account}.github.io/{lesson}/"

    return website_base_url


def get_remote_url(repo_dir):
    """
    In the episode markdown files, {{page.root}} is expanded to e.g. https://carpentries.github.io/instructor-training/
    :param repo:
    :return:
    """
    command = ['git', '-C', repo_dir, 'remote']
    remotes = subprocess.check_output(command).decode("ascii").split()
    pattern = '.*(swcarpentry|datacarpentry|librarycarpentry|carpentries)/([^.]+)\.git'
    for remote in remotes:
        command = ["git", "-C", repo_dir, "config", "--get", f"remote.{remote}.url"]
        remote_url = subprocess.check_output(command).decode("ascii").strip()
        match = re.match(pattern, remote_url)
        if match:
            break

    return remote_url


def substitute_internal_links(input_line, page_root_value):
    """
    Replace the page.root variable with the github pages URL.
    :param line:
    :return:
    """
    var_pattern = "(\{\{\s*page\.root\s*\}\}\/*)"
    matches = re.findall(var_pattern, input_line)
    for var in matches:
        input_line = re.sub(var_pattern, page_root_value, input_line)

    var_pattern = "(\{% link _episodes/(\w+-\w+)\.md %\})"
    matches = re.findall(var_pattern, input_line)
    for var in matches:
        input_line = re.sub(var_pattern, var[1], input_line)

    return input_line


def resolve_file_links(line, repo_blob_stem):
    """
    Replace links to within the repo with full URL to files
    :param line:
    :param repo_blob_stem:
    :return: file download link
    """
    pattern = "\(\.\.(/files/\S+?)\)" # use two sub-groups
    matches = re.findall(pattern, line)
    for match in matches:
        line = re.sub(pattern, "(" + repo_blob_stem + match + ")", line)
    return line

def replace_etherpad_with_shared_doc(line):
    """
    Replace references to etherpad with shared document
    :param line:
    :return:
    """
    line = re.sub('[Ee]therpad', 'shared document', line)
    return line

check_input_arguments()

lesson_dir = sys.argv[1]
yaml_config = os.path.join(lesson_dir, "_config.yml")
input_files = sorted(glob.glob(os.path.join(lesson_dir, "_episodes", "*.md")))
output_file = "exercises.md"
remote_url = get_remote_url(lesson_dir)
website_url = github_pages_from_remote(remote_url)

# Delete output file if it already exists - we're appending to it later
if os.path.exists(output_file) and os.path.isfile(output_file):
    os.remove(output_file)

for file in input_files:
    episode_title = "# " + os.path.splitext(os.path.basename(file))[0]

    with open(file) as f:
        content = f.readlines()

    # Go through content, looking for exercise markup
    ex_markup = "{: .challenge}"
    discuss_markup = "{: .discussion}"
    exercise_text = []
    for line_num, line in enumerate(content):
        if line.startswith(ex_markup) or line.startswith(discuss_markup):
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
