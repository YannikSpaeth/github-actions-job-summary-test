import argparse
import glob
import os
import re
import sys

import requests
from junitparser import Error, Failure, JUnitXml

# Embedded in the PR comment so we can find and update it instead of posting a new one each run.
MARKER    = "<!-- ci-test-summary -->"
SERVER    = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
API       = os.environ.get("GITHUB_API_URL",    "https://api.github.com")
WORKSPACE = os.environ.get("GITHUB_WORKSPACE",  "").rstrip("/")


def extract_gtest_failure(system_out, test_name):
    """Extract the assertion lines between [ RUN ] and [ FAILED ] from GTest's system_out."""
    capturing = False
    captured_lines = []

    for line in (system_out or "").splitlines():
        if f"[ RUN      ] {test_name}" in line:
            capturing = True
            continue
        if capturing:
            if f"[  FAILED  ] {test_name}" in line:
                break
            captured_lines.append(line)

    return "\n".join(captured_lines).strip()


def build_source_link(failure_text, repo, sha):
    """Parse the file:line header from a GTest failure and return a markdown link to that line on GitHub."""
    if not failure_text:
        return ""

    first_line = failure_text.strip().splitlines()[0]
    match = re.match(r'^(.+?):(\d+):\s+\w+', first_line)
    if not match:
        return ""

    absolute_path = match.group(1)
    line_number   = match.group(2)

    # Strip the runner's workspace prefix to get a repo-relative path
    if WORKSPACE and absolute_path.startswith(WORKSPACE):
        relative_path = absolute_path[len(WORKSPACE):].lstrip("/")
    else:
        relative_path = absolute_path

    if repo:
        url = f"{SERVER}/{repo}/blob/{sha}/{relative_path}#L{line_number}"
        return f"[{relative_path}:{line_number}]({url})"
    return f"{relative_path}:{line_number}"


def parse_xml_file(xml_path, platform, repo, sha):
    """Parse a CTest JUnit XML file and return (failures, passed_count, total_count)."""
    failures    = []
    passed_count = 0

    for suite in JUnitXml.fromfile(xml_path):
        for test_case in suite:
            if test_case.result and isinstance(test_case.result[0], (Failure, Error)):
                failure_text = extract_gtest_failure(test_case.system_out, test_case.name)
                # First line is the file:line header; the rest is the actual assertion output
                message_lines = failure_text.splitlines()
                message = "\n".join(message_lines[1:]).strip() if len(message_lines) > 1 else failure_text

                failures.append({
                    "name":    f"{suite.name}.{test_case.name}",
                    "link":    build_source_link(failure_text, repo, sha),
                    "message": message,
                })
            else:
                passed_count += 1

    total_count = passed_count + len(failures)
    return failures, passed_count, total_count


# --- Argument parsing ---

parser = argparse.ArgumentParser()
parser.add_argument("--xml-dir",   required=True,  help="Folder with JUnit XML files (searched recursively)")
parser.add_argument("--pr-number", default="",     help="PR number to comment on (empty = skip)")
parser.add_argument("--repo",      default="",     help="GitHub repository (owner/repo)")
parser.add_argument("--run-id",    default="",     help="GitHub Actions run ID")
parser.add_argument("--sha",       default="HEAD", help="Git commit SHA for source links")
args = parser.parse_args()


# --- Parse all XML files ---

xml_files = sorted(glob.glob(os.path.join(args.xml_dir, "**", "*.xml"), recursive=True))

if not xml_files:
    print(f"No XML files found in '{args.xml_dir}' — nothing to report.")
    sys.exit(0)

# Derive the platform name from the artifact folder, e.g.:
# xml-artifacts/test-results-ubuntu/test-results.xml  →  "ubuntu"
all_results = []

for xml_path in xml_files:
    parent_folder = os.path.basename(os.path.dirname(xml_path))
    platform = parent_folder.replace("test-results-", "") or os.path.splitext(os.path.basename(xml_path))[0]

    print(f"Parsing '{xml_path}' (platform: {platform}) ...")
    failures, passed, total = parse_xml_file(xml_path, platform, args.repo, args.sha)
    all_results.append((platform, failures, passed, total))
    print(f"  -> {passed}/{total} passed, {len(failures)} failed")


# --- Build markdown ---

run_url = f"{SERVER}/{args.repo}/actions/runs/{args.run_id}" if args.repo and args.run_id else ""

def result_icon(has_failures):
    return ":x:" if has_failures else ":white_check_mark:"

markdown_lines = []
markdown_lines.append(MARKER)
markdown_lines.append("## CI Test Results\n")
markdown_lines.append("| Platform | Result | Tests |")
markdown_lines.append("|----------|--------|-------|")

for platform, failures, passed, total in all_results:
    platform_cell = f"[{platform}]({run_url})" if run_url else platform
    markdown_lines.append(f"| {platform_cell} | {result_icon(failures)} | {passed}/{total} |")

markdown_lines.append("")
any_failures = False

for platform, failures, passed, total in all_results:
    if not failures:
        continue

    any_failures = True

    markdown_lines.append(f"### :x: {platform}\n")
    markdown_lines.append("| Test | Location |")
    markdown_lines.append("|------|----------|")

    for failure in failures:
        markdown_lines.append(f"| `{failure['name']}` | {failure['link']} |")

    markdown_lines.append("")
    markdown_lines.append("<details><summary>Full output</summary>\n")
    for failure in failures:
        if failure["message"]:
            markdown_lines.append(f"**`{failure['name']}`**")
            markdown_lines.append(f"```\n{failure['message']}\n```")
            markdown_lines.append("")
    markdown_lines.append("</details>\n")

if not any_failures:
    markdown_lines.append(":white_check_mark: **All tests passed on all platforms.**\n")

if run_url:
    markdown_lines.append(f"\n---\n_[Full CI run]({run_url}) · `{args.sha[:7]}`_")

comment_body = "\n".join(markdown_lines)


# --- Write to GitHub Actions job summary ---

step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
if step_summary_path:
    with open(step_summary_path, "a") as summary_file:
        # Strip the HTML marker — it's only needed for finding the PR comment
        summary_content = comment_body.replace(MARKER, "").strip()
        summary_file.write(summary_content + "\n")
    print("Written to GitHub Actions job summary.")
else:
    print("GITHUB_STEP_SUMMARY not set — skipping job summary write.")


# ---------------------------------------------------------------------------
# Post or update the PR comment
# ---------------------------------------------------------------------------

if not args.pr_number or not args.repo:
    print("No pull request number provided — skipping PR comment.")
    sys.exit(0)

token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if not token:
    print("ERROR: GH_TOKEN / GITHUB_TOKEN is not set.")
    sys.exit(1)

request_headers = {
    "Authorization":        f"Bearer {token}",
    "Accept":               "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

comments_url        = f"{API}/repos/{args.repo}/issues/{args.pr_number}/comments"
existing_comment_id = None

# Page through existing comments to find one we posted before (identified by MARKER)
for page in range(1, 10):
    response = requests.get(comments_url, headers=request_headers, params={"per_page": 100, "page": page})
    response.raise_for_status()
    comments = response.json()

    for comment in comments:
        if MARKER in comment.get("body", ""):
            existing_comment_id = comment["id"]
            break

    if existing_comment_id is not None or len(comments) < 100:
        break

if existing_comment_id is not None:
    print(f"Updating existing comment {existing_comment_id} ...")
    result = requests.patch(f"{API}/repos/{args.repo}/issues/comments/{existing_comment_id}",
                            headers=request_headers, json={"body": comment_body})
else:
    print("Posting new comment ...")
    result = requests.post(comments_url, headers=request_headers, json={"body": comment_body})

result.raise_for_status()
print(f"Done: {result.json().get('html_url', '')}")
