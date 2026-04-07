# Read XML File
# Parse errors with junitparser
# Output organized error summary in JSON

import argparse
import json
from junitparser import JUnitXml, Failure, Error
import os

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
        if case.result:
            if isinstance(case.result[0], Failure):
                status = "FAILED"
            elif isinstance(case.result[0], Error):
                status = "ERROR"
        suite_data["tests"].append({"name": case.name, "status": status})
    result["test_suites"].append(suite_data)

# JSON ausgeben
print(json.dumps(result, indent=2))
# Write to GitHub Actions job summary
with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
    f.write("## Test Results Summary\n\n```json\n")
    f.write(json.dumps(result, indent=2))
    f.write("\n```\n")
