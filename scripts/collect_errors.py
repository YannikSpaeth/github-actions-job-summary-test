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

# Command-line argument parsing
parser = argparse.ArgumentParser(description='Parse JUnit XML and summarize test results.')
parser.add_argument('xml_file', nargs='?', default='build/test-results.xml', help='Path to the JUnit XML file')
args = parser.parse_args()

# XML-Datei laden
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
                    msg = ""
                    if t.get("details"):
                        # Use message field if available, otherwise first line of text
                        raw = t["details"].get("message") or (t["details"].get("text") or "").strip().splitlines()[0] if t["details"].get("text") else ""
                        msg = raw.replace("|", "\\|").replace("\n", " ")
                    f.write(f"| {t['name']} | {t['status']} | {msg} |\n")
                f.write("\n")

                f.write("<details><summary>Full failure output</summary>\n\n")
                for t in failures:
                    if t.get("details", {}).get("text"):
                        f.write(f"**{t['name']}**\n```\n{t['details']['text'].strip()}\n```\n\n")
                f.write("</details>\n\n")
            else:
                f.write("All tests passed.\n\n")
