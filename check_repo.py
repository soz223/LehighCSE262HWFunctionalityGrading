import gitlab
import sys
import os
from urllib.parse import urlparse
from collections import defaultdict
from datetime import datetime

from datetime import datetime

def list_commit_date_range(project, ref='main', start_date_str='2024-08-15'):
    try:
        # Parse the provided start date
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        
        # Retrieve the list of commits for the specified branch
        commits = project.commits.list(ref_name=ref, all=True)
        
        # Filter commits after the provided start date
        filtered_commits = [commit for commit in commits if datetime.strptime(commit.created_at, "%Y-%m-%dT%H:%M:%S.%f%z").date() > start_date.date()]
        
        if not filtered_commits:
            print(f"No commits found after {start_date_str}.")
            return
        
        # Get the date range of the filtered commits
        first_commit_date = datetime.strptime(filtered_commits[-1].created_at, "%Y-%m-%dT%H:%M:%S.%f%z").date()
        last_commit_date = datetime.strptime(filtered_commits[0].created_at, "%Y-%m-%dT%H:%M:%S.%f%z").date()
        
        print(f"Commit date range after {start_date_str}: {first_commit_date} to {last_commit_date}")
        return filtered_commits
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Failed to retrieve commits: {e}")
    except Exception as e:
        print(f"An error occurred while listing commit date range: {e}")




def filter_commits_by_date_range(commits, start_date_str, end_date_str):
    try:
        # Parse the provided start and end dates
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        # Filter commits within the provided date range
        filtered_commits = [
            commit for commit in commits
            if start_date.date() <= datetime.strptime(commit.created_at, "%Y-%m-%dT%H:%M:%S.%f%z").date() <= end_date.date()
        ]
        
        if not filtered_commits:
            print(f"No commits found between {start_date_str} and {end_date_str}.")
        else:
            print(f"Commits between {start_date_str} and {end_date_str}: {len(filtered_commits)} commit(s) found.")
        
        return filtered_commits
    except Exception as e:
        print(f"An error occurred while filtering commits by date range: {e}")
        return []
    

# Define required files
REQUIRED_FILES = ['README.md']

# Replace with your GitLab URL and ensure the private token is set as an environment variable
GITLAB_URL = 'http://gitlab.cse.lehigh.edu/'
PRIVATE_TOKEN = 'AQvzxMwjZfbG1u4TSexu'

if not PRIVATE_TOKEN:
    print("Error: GITLAB_PRIVATE_TOKEN environment variable not set.")
    sys.exit(1)

# Function to initialize GitLab connection
def init_gitlab(url, token):
    try:
        gl = gitlab.Gitlab(url, private_token=token)
        gl.auth()  # Authenticate
        print("Successfully authenticated with GitLab.")
        return gl
    except gitlab.exceptions.GitlabAuthenticationError:
        print("Authentication failed. Please check your access token.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while connecting to GitLab: {e}")
        sys.exit(1)

# Function to get a project by its URL
def get_project(gl, project_url):
    try:
        parsed_url = urlparse(project_url)
        path = parsed_url.path.strip('/')
        project = gl.projects.get(path)
        print(f"Accessed project: {project.name}")
        return project
    except gitlab.exceptions.GitlabGetError:
        print("Failed to retrieve the project. Please check the repository URL.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while retrieving the project: {e}")
        sys.exit(1)

import base64

# Function to count the number of tests in 'tests/lex.rs'
def count_tests_in_lex_rs(project, ref='main', file_path='tests/lex.rs'):
    try:
        # Get the file contents from the repository (base64 encoded)
        file = project.files.get(file_path=file_path, ref=ref)
        file_content = base64.b64decode(file.content).decode('utf-8')
        
        # Count the number of tests (using Rust's #[test] attribute as a marker)
        test_count = file_content.count("#[test]")
        print(f"Number of tests in '{file_path}': {test_count}")
        return test_count
    except gitlab.exceptions.GitlabGetError:
        print(f"Failed to retrieve the file '{file_path}'. Make sure it exists.")
        return 0
    except Exception as e:
        print(f"An error occurred while counting tests in '{file_path}': {e}")
        return 0


# Function to check how many tests passed in the last pipeline
def count_passed_tests_in_ci(project, ref='main'):
    try:
        # Get the latest pipeline
        pipelines = project.pipelines.list(ref=ref, all=True)
        if not pipelines:
            print(f"No CI/CD pipelines found for branch '{ref}'.")
            return 0
        
        # Get the latest pipeline's jobs
        latest_pipeline = pipelines[0]
        jobs = latest_pipeline.jobs.list()

        # Count the number of passed test jobs (using status 'success' and assuming test-related jobs have 'test' in their name)
        passed_tests = 0
        for job in jobs:
            if 'test' in job.name.lower() and job.status == 'ok':
                passed_tests += 1

        return passed_tests
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Failed to retrieve pipelines or jobs: {e}")
        return 0
    except Exception as e:
        print(f"An error occurred while counting passed tests in CI: {e}")
        return 0



# print CI/CD pipeline log

import re

def analyze_test_results(log):
    # Regular expressions to capture test results
    total_tests_pattern = re.compile(r"running (\d+) tests")
    passed_tests_pattern = re.compile(r"test result: ok\. (\d+) passed; (\d+) failed")
    individual_pass_pattern = re.compile(r"test .+ \.\.\. ok")
    individual_fail_pattern = re.compile(r"test .+ \.\.\. FAILED")

    # Counters for total, passed, and failed tests
    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    # Analyze each line in the log
    for line in log.splitlines():
        if total_tests_match := total_tests_pattern.search(line):
            total_tests = int(total_tests_match.group(1))
        elif passed_tests_match := passed_tests_pattern.search(line):
            passed_tests += int(passed_tests_match.group(1))
            failed_tests += int(passed_tests_match.group(2))
        elif individual_pass_pattern.search(line):
            passed_tests += 1
        elif individual_fail_pattern.search(line):
            failed_tests += 1

    # If we haven't found the total tests from the first pattern, calculate it from passed + failed
    if total_tests == 0:
        total_tests = passed_tests + failed_tests

    return total_tests, passed_tests, failed_tests

def print_pipeline_log(project, pipeline_id):
    try:
        pipeline = project.pipelines.get(pipeline_id)
        jobs = pipeline.jobs.list()
        
        for job in jobs:
            # Retrieve the full job object using its ID to access complete data
            job_full = project.jobs.get(job.id)
            print(f"Job ID: {job_full.id}, Name: {job_full.name}, Status: {job_full.status}")
            
            # Process only if the job has failed or as required
            log = job_full.trace()
            if log:
                # Decode the log from bytes to a string
                log = log.decode('utf-8')
                
                # Analyze the test results from the log
                total_tests, passed_tests, failed_tests = analyze_test_results(log)
                
                print(f"Test Analysis for Job ID {job_full.id}:")
                print(f"  Total tests run: {total_tests}")
                print(f"  Tests passed: {passed_tests}")
                print(f"  Tests failed: {failed_tests}")
                return total_tests, passed_tests, failed_tests
                
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Failed to retrieve pipeline or job: {e}")
    except Exception as e:
        print(f"An error occurred while printing pipeline log: {e}")


# Function to list available branches
def list_branches(project):
    try:
        branches = project.branches.list()
        print("Available branches:")
        for branch in branches:
            print(f"  - {branch.name}")
    except Exception as e:
        print(f"Failed to list branches: {e}")

# Function to get the default branch
def get_default_branch(project):
    try:
        return project.default_branch
    except Exception as e:
        print(f"Failed to get default branch: {e}")
        return 'master'  # Fallback to 'master' if detection fails

# Function to list repository contents
def list_repo_contents(project, ref='main', path=''):
    try:
        items = project.repository_tree(ref=ref, path=path, all=True)
        if not items:
            print("  No items found in the repository.")
            return
        for item in items:
            item_type = item['type']
            item_name = item['name']
            if item_type == 'tree':
                print(f"  📁 {item_name}/")
            elif item_type == 'blob':
                print(f"  📄 {item_name}")
            else:
                print(f"  {item_type.upper()} {item_name}")
    except gitlab.exceptions.GitlabGetError as e:
        print(f"  Failed to retrieve repository contents: {e}")
    except Exception as e:
        print(f"  An error occurred while listing repository contents: {e}")

# Function to get commit count
def get_commit_count(project, ref='main'):
    try:
        commits = project.commits.list(ref_name=ref, all=True)
        commit_count = len(commits)
        print(f"Total number of commits on branch '{ref}': {commit_count}")
        return commit_count
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Failed to retrieve commits: {e}")
        return 0
    except Exception as e:
        print(f"An error occurred while fetching commits: {e}")
        return 0

# Function to list commit details
def list_commit_details(project, ref='main'):
    try:
        commits = project.commits.list(ref_name=ref, all=True)
        print(f"\nCommit Details for branch '{ref}':")
        for commit in commits:
            print(f"Commit ID: {commit.id}")
            print(f"Author: {commit.author_name} <{commit.author_email}>")
            print(f"Date: {commit.created_at}")
            print(f"Message: {commit.message}")
            print("-" * 40)
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Failed to retrieve commit details: {e}")
    except Exception as e:
        print(f"An error occurred while listing commit details: {e}")

# Function to get commits per author
def get_commits_per_author(project, ref='main'):
    try:
        commits = project.commits.list(ref_name=ref, all=True)
        author_commit_count = defaultdict(int)
        for commit in commits:
            author = commit.author_name
            author_commit_count[author] += 1

        print(f"\nCommits per author on branch '{ref}':")
        for author, count in author_commit_count.items():
            print(f"{author}: {count} commit(s)")
        return author_commit_count
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Failed to retrieve commits: {e}")
        return {}
    except Exception as e:
        print(f"An error occurred while fetching commits per author: {e}")
        return {}

# Function to get commit frequency
def get_commit_frequency(project, ref='main'):
    try:
        commits = project.commits.list(ref_name=ref, all=True)
        commit_dates = defaultdict(int)
        for commit in commits:
            # Parse the commit date
            # date = datetime.strptime(commit.created_at, r"%Y-%m-%dT%H:%M:%SZ").date()
            # format is like 2024-09-08T21:57:57.000-04:00
            date = datetime.strptime(commit.created_at, r"%Y-%m-%dT%H:%M:%S.%f%z").date()
            commit_dates[date] += 1

        print(f"\nCommit frequency on branch '{ref}':")
        for date, count in sorted(commit_dates.items()):
            print(f"{date}: {count} commit(s)")
        return commit_dates
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Failed to retrieve commits: {e}")
        return {}
    except Exception as e:
        print(f"An error occurred while calculating commit frequency: {e}")
        return {}

# Function to check required files
def check_required_files(project, ref='main', required_files=REQUIRED_FILES):
    try:
        files = project.repository_tree(ref=ref, all=True)
        file_names = [file['name'] for file in files if file['type'] == 'blob']
        missing_files = [file for file in required_files if file not in file_names]

        if not missing_files:
            print("\nAll required files are present.")
        else:
            print("\nMissing required files:")
            for file in missing_files:
                print(f"  - {file}")
        return missing_files
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Failed to retrieve repository files: {e}")
        return required_files
    except Exception as e:
        print(f"An error occurred while checking required files: {e}")
        return required_files

# Function to list merge requests
def list_merge_requests(project):
    try:
        merge_requests = project.mergerequests.list(state='all', all=True)
        if not merge_requests:
            print("\nNo merge requests found.")
            return []
        print("\nMerge Requests:")
        for mr in merge_requests:
            print(f"ID: {mr.iid}, Title: {mr.title}, State: {mr.state}, Author: {mr.author['name']}")
        return merge_requests
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Failed to retrieve merge requests: {e}")
        return []
    except Exception as e:
        print(f"An error occurred while listing merge requests: {e}")
        return []

# Function to check CI/CD status
def check_ci_status(project, ref='main'):
    try:
        pipelines = project.pipelines.list(ref=ref, all=True)
        if not pipelines:
            print(f"\nNo CI/CD pipelines found for branch '{ref}'.")
            return []
        print(f"\nCI/CD Pipelines for branch '{ref}':")
        for pipeline in pipelines:
            print(f"ID: {pipeline.id}, Status: {pipeline.status}, Created At: {pipeline.created_at}")
        
        print('\n\n\n')
        print('-'*50)
        if pipelines[0].status == 'success':
            print('Latest CI/CD pipeline passed')
        else:
            print('Latest CI/CD pipeline failed')
        print('-'*50)
        return pipelines
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Failed to retrieve pipelines: {e}")
        return []
    except Exception as e:
        print(f"An error occurred while checking CI/CD status: {e}")
        return []

import base64
import os
from urllib.parse import urlparse

# Function to parse the repository URL and extract username and homework number
def parse_repo_url(repo_url):
    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip('/').split('/')
    username = path_parts[0].split('-')[0]
    hw_part = path_parts[1]
    type_string = hw_part.split('-')[0]
    homework_number = hw_part.split('-')[-1]
    # local_folder_name = f"{username}-hw{homework_number}"
    # local_folder_name = f"repo/homework-{homework_number}/{username}-cse262/homework-{homework_number}"

    # quiz
    # local_folder_name = f"repo/quiz-{homework_number}/{username}-cse262/quiz-{homework_number}"
    local_folder_name = f"repo/{type_string}-{homework_number}/{username}-cse262/{type_string}-{homework_number}"
    return local_folder_name
import base64
import os

import os
import base64
import mimetypes

def download_project(project, ref='main', folder_path='', local_dir='./'):
    try:
        # Create the local directory if it doesn't exist
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
        
        # Retrieve the folder contents from the repository
        items = project.repository_tree(ref=ref, path=folder_path, all=True)
        
        if not items:
            print("Failure")
            return
        
        # Process each item in the folder
        for item in items:
            if item['type'] == 'blob':  # It's a file
                file_path = f"{folder_path}/{item['name']}".lstrip('/') if folder_path else item['name']
                file = project.files.get(file_path=file_path, ref=ref)
                
                # Decode the file content from base64
                file_content = base64.b64decode(file.content)
                
                # Determine the file type (text or binary)
                mime_type, _ = mimetypes.guess_type(item['name'])
                is_text = mime_type and mime_type.startswith('text')
                
                # Write the file content to the local file
                local_file_path = os.path.join(local_dir, item['name'])
                
                # Write as text if it's a text file, else write as binary
                if is_text:
                    with open(local_file_path, 'w', encoding='utf-8') as f:
                        f.write(file_content.decode('utf-8'))
                else:
                    with open(local_file_path, 'wb') as f:
                        f.write(file_content)
            
            elif item['type'] == 'tree':  # It's a directory
                subfolder_path = os.path.join(local_dir, item['name'])
                download_project(project, ref=ref, folder_path=f"{folder_path}/{item['name']}".lstrip('/'), local_dir=subfolder_path)
                
    except Exception as e:
        print(f"An error occurred: {e}")

        
def main():
    if len(sys.argv) != 2:
        print("Usage: python check_repo.py <student_repo_url>")
        sys.exit(1)

    student_repo_url = sys.argv[1]

    # Initialize GitLab connection
    gl = init_gitlab(GITLAB_URL, PRIVATE_TOKEN)

    # Get the project
    project = get_project(gl, student_repo_url)

    # List available branches
    list_branches(project)

    # Get the default branch
    default_branch = get_default_branch(project)
    print(f"\nDefault branch detected: {default_branch}")

    # List repository contents
    print(f"\nContents of the repository '{project.name}':")
    list_repo_contents(project, ref=default_branch)

    # Count the number of tests in 'tests/lex.rs'
    test_count = count_tests_in_lex_rs(project, ref=default_branch)

    print(f"\nNumber of tests in 'tests/lex.rs': {test_count}")

    # Check how many tests passed in the last pipeline
    passed_tests = count_passed_tests_in_ci(project, ref=default_branch)

    print(f"Number of passed test jobs in the latest CI/CD pipeline: {passed_tests}")
    

    # result_folder = './cicd/' + {type_string}-{homework_number}
    parsed_url = urlparse(student_repo_url)
    path_parts = parsed_url.path.strip('/').split('/')
    type_string = path_parts[1].split('-')[0]
    homework_number = path_parts[1].split('-')[-1]
    result_folder = f'./cicd/{type_string}-{homework_number}'
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)





    # Get commit count
    commit_count = get_commit_count(project, ref=default_branch)

    # List commit details
    list_commit_details(project, ref=default_branch)



    # result path: cicd/homework-2/results.txt
    # result format, each line: <student_username>,<number_of_tests>,<number_of_passed_tests>
    # with open('./cicd/homework-2/results.txt', 'a') as f:
    print('home work number:', homework_number)
    print('commit count:', commit_count)
    # with open(f'{result_folder}/results.txt', 'a') as f:
    #     # if homework_number == 3:
    #     f.write(f"{student_repo_url},{commit_count}\n")
    #     f.write(f'all_tests,{test_count} passed_tests,{passed_tests}\n\n\n')



    # Get commits per author
    commits_per_author = get_commits_per_author(project, ref=default_branch)

    # Get commit frequency
    commit_frequency = get_commit_frequency(project, ref=default_branch)

    # Check for required files
    missing_files = check_required_files(project, ref=default_branch)

    # List merge requests
    merge_requests = list_merge_requests(project)

    local_folder_name = parse_repo_url(student_repo_url)

    download_project(project, ref=default_branch, folder_path='', local_dir=local_folder_name)

    # List commit date range after 2024-08-15
    filtered_commits = list_commit_date_range(project, ref=default_branch, start_date_str='2024-08-15')

    # If filtered commits exist, filter them further by a specific date range
    if filtered_commits:
        start_date_str = '2024-09-01'
        end_date_str = '2024-09-30'
        filter_commits_by_date_range(filtered_commits, start_date_str, end_date_str)
    

    # Check CI/CD status
    pipelines = check_ci_status(project, ref=default_branch)

    # Print CI/CD pipeline log

    # if type_string is quiz, then no more print_pipeline_log
    if type_string != 'quiz':
        total_tests, passed_tests, failed_tests = print_pipeline_log(project, pipelines[0].id)
    else:
        total_tests, passed_tests, failed_tests = 0, 0, 0


    # total_tests, passed_tests, failed_tests = print_pipeline_log(project, pipelines[0].id)


    with open(f'{result_folder}/results.txt', 'a') as f:

        username = student_repo_url.replace("http://gitlab.cse.lehigh.edu/", "").split('-')[0]

        f.write('-'*10 + ' ' + username + ' ' + '-'*10 + '\n')
        f.write(f"{student_repo_url},{commit_count}\n")
        f.write(f'all_tests,{total_tests} passed_tests,{passed_tests} failed_tests,{failed_tests}\n')
        f.write('-'*10 + ' ' + username + ' ' + '-'*10 + '\n\n\n')






if __name__ == "__main__":
    main()