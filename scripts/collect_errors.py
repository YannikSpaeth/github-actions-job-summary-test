# Read XML File
# Parse errors with junitparser
# Output organized error summary

from junitparser import JUnitXml, Failure, Error

# XML-Datei laden
xml = JUnitXml.fromfile('gtest_results.xml')

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
