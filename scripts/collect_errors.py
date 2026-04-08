# Read XML File
# Parse errors with junitparser
# Output organized error summary in JSON

import argparse
import json
import re
from junitparser import JUnitXml, Failure, Error
import os


def extract_failure_details(system_out: str, test_name: str) -> str:
    """Extract the failure message lines from GTest system-out output.
    
    Grabs the lines between '[ RUN      ] test_name' and '[  FAILED  ] test_name',
    which contain the file:line reference and assertion details.
    """
    if not system_out:
        return ""
    lines = system_out.splitlines()
    capturing = False
    captured = []
    run_marker = f"[ RUN      ] {test_name}"
    failed_marker = f"[  FAILED  ] {test_name}"
    for line in lines:
        if run_marker in line:
            capturing = True
            continue
        if capturing:
            if failed_marker in line:
                break
            captured.append(line)
    return "\n".join(captured).strip()

def make_source_link(text: str) -> str:
    """Parse 'file:line: Failure' from the first line of GTest output and return a markdown link."""
    if not text:
        return ""
    first_line = text.strip().splitlines()[0]
    # GTest format: /abs/path/to/file.cpp:29: Failure
    match = re.match(r'^(.+?):(\d+):\s+\w+', first_line)
    if not match:
        return first_line
    abs_path, line_no = match.group(1), match.group(2)

    # Strip workspace prefix to get a repo-relative path
    workspace = os.environ.get('GITHUB_WORKSPACE', '').rstrip('/')
    rel_path = abs_path[len(workspace):].lstrip('/') if workspace and abs_path.startswith(workspace) else abs_path

    # Build a GitHub blob link if we have repo info
    server = os.environ.get('GITHUB_SERVER_URL', 'https://github.com')
    repo   = os.environ.get('GITHUB_REPOSITORY', '')
    sha    = os.environ.get('GITHUB_SHA', 'HEAD')
    if repo:
        url = f"{server}/{repo}/blob/{sha}/{rel_path}#L{line_no}"
        return f"[{rel_path}:{line_no}]({url})"
    return f"{rel_path}:{line_no}"

# Command-line argument parsing
parser = argparse.ArgumentParser(description='Parse JUnit XML and summarize test results.')
parser.add_argument('xml_file', nargs='?', default='build/test-results.xml', help='Path to the JUnit XML file')
args = parser.parse_args()

# XML-Datei laden
if not os.path.exists(args.xml_file):
    print(f"ERROR: XML file not found: {args.xml_file}", flush=True)
    summary_path = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_path:
        with open(summary_path, 'a') as f:
            f.write(f"## Test Results Summary\n\n**No XML file found at `{args.xml_file}`** — tests may not have run.\n")
    raise SystemExit(1)

xml = JUnitXml.fromfile(args.xml_file)

# Datenstruktur für JSON
result = {"test_suites": []}

# Über Testsuites und Testcases iterieren
for suite in xml:
    suite_data = {"name": suite.name, "tests": []}
    for case in suite:
        status = "PASSED"
        details = None
        if case.result:
            result_item = case.result[0]
            if isinstance(result_item, Failure):
                status = "FAILED"
            elif isinstance(result_item, Error):
                status = "ERROR"
            failure_text = extract_failure_details(case.system_out, case.name)
            details = {
                "message": result_item.message,
                "text": failure_text or result_item.text,
            }
        test_entry = {"name": case.name, "status": status}
        if details:
            test_entry["details"] = details
        suite_data["tests"].append(test_entry)
    result["test_suites"].append(suite_data)

# JSON ausgeben
print(json.dumps(result, indent=2))

# Write to GitHub Actions job summary
summary_path = os.environ.get('GITHUB_STEP_SUMMARY')
if summary_path:
    with open(summary_path, 'a') as f:
        f.write("## Test Results Summary\n\n")

        for suite in result["test_suites"]:
            failures = [t for t in suite["tests"] if t["status"] in ("FAILED", "ERROR")]
            passed = sum(1 for t in suite["tests"] if t["status"] == "PASSED")
            total = len(suite["tests"])

            f.write(f"### {suite['name']} ({passed}/{total} passed)\n\n")

            if failures:
                f.write("| Test | Status | What went wrong |\n")
                f.write("|------|--------|------------------|\n")
                for t in failures:
                    msg = make_source_link(t.get("details", {}).get("text", ""))
                    f.write(f"| {t['name']} | {t['status']} | {msg} |\n")
                f.write("\n")

                f.write("<details><summary>Full failure output</summary>\n\n")
                for t in failures:
                    if t.get("details", {}).get("text"):
                        f.write(f"**{t['name']}**\n```\n{t['details']['text'].strip()}\n```\n\n")
                f.write("</details>\n\n")
            else:
                f.write("All tests passed.\n\n")
