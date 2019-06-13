from rflint.common import SuiteRule, ERROR, WARNING
from rflint.parser import SettingTable
import re

"""
5G TAF Coding Rules  - Test Suites Part:
1. <FeatureFolder> shall correspond to the FeatureId under test, e.g.: "5GC000165"
2. Name of robot file shall have file suffix as named as ".robot"
3. Don't use ${CURDIR} or dot when importing from parent directory.
4. Use dot when importing from the same directory
5. Docstring shall have purpose of test suite and Author name. If author name is different from the maintainer,\\ 
   then also a contact shall be listed.
6. Resource/libraries shall be classified if they are still maintained or out-of-maintenance.\\ 
   This can be done with a documentation tag: [THIS FILE IS DEPRECATED]. 
   Documentation tag can be located anywhere within the docstring.\\
Modified: 6/12/2019 Carson Wu
"""


def normalize_name(string):
    '''convert to lowercase, remove spaces and underscores'''
    return string.replace(" ", "").replace("_", "").lower()

class RequiredRobotFileSuffxAndFolder(SuiteRule):
    """
    Rule 2: Name of robot file shall have file suffix as named as ".robot"
    Author: Carson Wu
    Modified: 6/12/2019
    """
    severity = ERROR

    def apply(self, suite):
        if ".robot" not in suite.path:
            self.report(suite, "Required file suffix is \".robot\"", 0)
        if "5GC" not in suite.path:
            self.report(suite, "Required Parent folder is \"5GC*\"", 0)


class RequirdNoCurdirInImporting(SuiteRule):
    """
    Rule 3: Don't use ${CURDIR} or dot when importing from parent directory.
    Author: Carson Wu
    Modified: 6/12/2019
    """
    severity = ERROR

    def apply(self, suite):
        for table in suite.tables:
            if isinstance(table, SettingTable):
                for row in table.rows:
                    if row[0] == "Resource":
                        if "${CURDIR}" in row[1]:
                            self.report(suite, "Don't use ${CURDIR}", row.linenumber)



class RequiredAutherInfo(SuiteRule):
    """
    Rule 5: Docstring
    Docstring shall have purpose of test suite and Author name
    If author name is different from the maintainer,then also a contact shall be listed.
    Author: Carson Wu
    Modified: 6/12/2019
    """
    severity = ERROR

    def apply(self, suite):
        for table in suite.tables:
            if isinstance(table, SettingTable):
                AuthorFlag = False
                ContactFlag = False
                for row in table.rows:
                    for str in row:
                        if any(name in str.lower() for name in ["author", "name", "modified"]):
                            AuthorFlag = True
                        if any(name in str.lower() for name in ["contact", "mail", "team"]):
                            ContactFlag = True
                if AuthorFlag == False:
                    self.report(suite, "Author name is needed", 1)
                if ContactFlag == False:
                    self.report(suite, "Contact list is needed", 1)



class PeriodInSuiteName(SuiteRule):
    '''Warn about periods in the suite name
    
    Since robot uses "." as a path separator, using a "." in a suite
    name can lead to ambiguity. 
    '''
    severity = WARNING
    
    def apply(self,suite):
        if "." in suite.name:
            self.report(suite, "'.' in suite name '%s'" % suite.name, 0)

class InvalidTable(SuiteRule):
    '''Verify that there are no invalid table headers'''
    severity = WARNING

    def apply(self, suite):
        for table in suite.tables:
            if (not re.match(r'^(settings?|metadata|(test )?cases?|(user )?keywords?|variables?)$', 
                             table.name, re.IGNORECASE)):
                self.report(suite, "Unknown table name '%s'" % table.name, table.linenumber)


class DuplicateKeywordNames(SuiteRule):
    '''Verify that no keywords have a name of an existing keyword in the same file'''
    severity = ERROR

    def apply(self, suite):
        cache = []
        for keyword in suite.keywords:
            # normalize the name, so we catch things like
            # Smoke Test vs Smoke_Test, vs SmokeTest, which
            # robot thinks are all the same
            name = normalize_name(keyword.name)
            if name in cache:
                self.report(suite, "Duplicate keyword name '%s'" % keyword.name, keyword.linenumber)
            cache.append(name)

class DuplicateTestNames(SuiteRule):
    '''Verify that no tests have a name of an existing test in the same suite'''
    severity = ERROR

    def apply(self, suite):
        cache = []
        for testcase in suite.testcases:
            # normalize the name, so we catch things like
            # Smoke Test vs Smoke_Test, vs SmokeTest, which
            # robot thinks are all the same
            name = normalize_name(testcase.name)
            if name in cache:
                self.report(suite, "Duplicate testcase name '%s'" % testcase.name, testcase.linenumber)
            cache.append(name)

class RequireSuiteDocumentation(SuiteRule):
    '''Verify that a test suite has documentation'''
    severity=WARNING

    def apply(self, suite):
        for table in suite.tables:
            if isinstance(table, SettingTable):
                for row in table.rows:
                    if row[0].lower() == "documentation":
                        return
        # we never found documentation; find the first line of the first
        # settings table, default to the first line of the file
        linenum = 1
        for table in suite.tables:
            if isinstance(table, SettingTable):
                linenum = table.linenumber + 1
                break

        self.report(suite, "No suite documentation", linenum)
            
class TooManyTestCases(SuiteRule):
    '''
    Should not have too many tests in one suite. 

    The exception is if they are data-driven.

    https://code.google.com/p/robotframework/wiki/HowToWriteGoodTestCases#Test_suite_structure

    You can configure the maximum number of tests. The default is 10. 
    '''
    severity = WARNING
    max_allowed = 10

    def configure(self, max_allowed):
        self.max_allowed = int(max_allowed)

    def apply(self, suite):
        # check for template (data-driven tests)
        for table in suite.tables:
            if isinstance(table, SettingTable):
                for row in table.rows:
                    if row[0].lower() == "test template":
                        return
        # we didn't find a template, so these aren't data-driven
        testcases = list(suite.testcases)
        if len(testcases) > self.max_allowed:
            self.report(
                suite, "Too many test cases (%s > %s) in test suite"
                % (len(testcases), self.max_allowed), testcases[self.max_allowed].linenumber
            )
