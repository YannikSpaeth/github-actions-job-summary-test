# Read XML File
# Parse errors with junitparser
# Output organized error summary

import argparse
from junitparser import JUnitXml, Failure, Error

# Command-line argument parsing
parser = argparse.ArgumentParser(description='Parse JUnit XML and summarize test results.')
parser.add_argument('xml_file', help='Path to the JUnit XML file')
args = parser.parse_args()

# XML-Datei laden
xml = JUnitXml.fromfile(args.xml_file)

# Über Testsuites und Testcases iterieren
for suite in xml:
    print(f"Suite: {suite.name}")
    for case in suite:
        status = "PASSED"
        if case.result:
            if isinstance(case.result[0], Failure):
                status = "FAILED"
            elif isinstance(case.result[0], Error):
                status = "ERROR"

        print(f"  Test: {case.name} -> {status}")
