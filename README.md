

# README

## Overview

This code is designed to automate the process of checking multiple students’ GitLab repositories for certain criteria (such as required files, tests, or CI/CD results). It works by reading a list of participants from a file, constructing their repository URLs, and then invoking a separate `check_repo.py` script to analyze each repository.

It can evaluate students' work by reading the commit history and the CI/CD pipeline pass situation. It can download the project and `cargo run` them to do the running locally in batch. To get started, please go to `grading-hw2.ipynb` (since in Fall 2024, HW1 in CSE262 has no CI/CD pipeline yet while HW2 and later assignments do).

The main idea is:

1. Read participant identifiers from `participants.txt`.
2. For each participant, form the appropriate GitLab repository URL.
3. Run `check_repo.py` against that repository.
4. If `check_repo.py` encounters an error, report it and continue with the next participant.

## Key Functional Steps

### 1. Input (Participants List)

The code expects a `participants.txt` file, where each line corresponds to a participant’s username or email. From this input, the code:

* Reads all participant entries line-by-line.
* Removes trailing newlines to obtain clean participant identifiers.

### 2. Constructing Repository URLs

Each participant is assumed to follow a consistent repository naming convention (e.g., `username-cse262/homework-1` on GitLab). The script constructs the repository URL by combining a GitLab base URL, the participant’s username, and a homework identifier.

**Example:**

```
http://gitlab.cse.lehigh.edu/<username>-cse262/homework-1
```

### 3. External Analysis Script – `check_repo.py`

This file leverages `check_repo.py` to perform the heavy lifting. The `check_repo.py` script (not shown here in detail) presumably:

* Connects to GitLab using the provided URL and token.
* Checks the repository for required files.
* Counts tests.
* Validates CI/CD pipelines.
* Generates a results file.

From this script’s perspective, you only need to know that `check_repo.py` analyzes a given repository and exits with a non-zero code if something goes wrong.

### 4. Error Handling and Continuous Execution

After calling `check_repo.py`, the script checks the returned status code:

* If `check_repo.py` fails, it prints an error message specific to that participant’s repository and moves on to the next one.
* If it succeeds, it prints the return code (typically `0` for success).

This ensures that one problematic repository does not halt the entire batch process.

## How to Use

1. **Prepare the Participants File:**
   Create a file named `participants.txt` and list one participant (username or email prefix) per line. For example:

   ```
   soz223
   abc123
   xyz789
   ...
   ```
2. **Adjust Homework Number (If Needed):**
   In the code, the repository URL is hardcoded to `homework-1`. If you need to check a different homework assignment, update the URL part accordingly:

   ```python
   repo_url = f"http://gitlab.cse.lehigh.edu/{people}-cse262/homework-2"
   ```
3. **Configure GitLab Private Token:**
   The scripts require a GitLab **Private Token** to authenticate and access repositories. Follow these steps to set it up:

   * **Obtain a Private Token:**

     * Log in to your GitLab account.
     * Navigate to [Personal Access Tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html).
     * Generate a new token with the necessary scopes (e.g., `read_repository`, `api`).
     * **Keep this token secure and do not share it publicly.**
   * **Set the Token in `check_repo.py`:**
     Open `check_repo.py` and locate the token configuration section. Insert your token as shown below:

     ```python
     PRIVATE_TOKEN = 'YOUR_TOKEN_AT_HERE'  # Put your token here. You can get it from your GitLab account: https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html
     ```

     **Security Best Practices:**

     * **Do Not Hardcode Tokens:** Instead of hardcoding the token in the script, consider using environment variables for enhanced security.
     * **Using Environment Variables:**
       * **Set the Environment Variable:**
         ```bash
         export GITLAB_PRIVATE_TOKEN='YOUR_TOKEN_AT_HERE'
         ```
       * **Modify `check_repo.py` to Use the Environment Variable:**
         ```python
         import os

         PRIVATE_TOKEN = os.getenv('GITLAB_PRIVATE_TOKEN')
         if not PRIVATE_TOKEN:
             raise ValueError("GitLab Private Token not found. Please set the GITLAB_PRIVATE_TOKEN environment variable.")
         ```
4. **Run the Code:**
   From the command line, simply run:

   ```bash
   python check_multiple_repos.py
   ```

   *(Assuming the above code is saved in `check_multiple_repos.py`)*
5. **Examine Output:**
   The script will output the status for each participant. If `check_repo.py` encounters an error for a participant’s repository, you’ll see an error message. Otherwise, you’ll see a success indicator (return code `0`).

## Integration Notes

* **Ensure `check_repo.py` is Accessible:**
  * Make sure `check_repo.py` is in the same directory as `check_multiple_repos.py` or is included in the system’s PATH.
* **GitLab Configuration:**
  * Verify that `check_repo.py` is correctly configured with the GitLab URL and the  **Private Token** .
* **Review Output Files:**
  * Examine the output files generated by `check_repo.py` (if any) for detailed results of each repository check. This might include test counts, CI/CD status, and required file presence.

By following the steps above, you can streamline the process of validating multiple students’ homework submissions against a standard set of repository requirements.
