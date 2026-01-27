/**
 * Legacy URL Fragment Redirect Handler
 *
 * This script handles redirects from legacy single-page User Guide URLs
 * (RobotFrameworkUserGuide.html#AnchorName) to the new multi-page structure.
 *
 * When a user visits the new site with a legacy fragment identifier,
 * this script maps it to the appropriate page and anchor in the new structure.
 */

(function() {
    'use strict';

    // Mapping of legacy anchor names to new URLs
    // Format: 'LegacyAnchor': 'new-page-path#new-anchor'
    const LEGACY_ANCHOR_MAP = {
        // === GETTING STARTED ===
        'Introduction': 'getting-started/introduction/',
        'WhyRobotFramework': 'getting-started/introduction/#why-robot-framework',
        'High-levelarchitecture': 'getting-started/introduction/#high-level-architecture',
        'HighLevelArchitecture': 'getting-started/introduction/#high-level-architecture',
        'Screenshots': 'getting-started/introduction/#screenshots',
        'Gettingmoreinformation': 'getting-started/introduction/#getting-more-information',
        'Projectpages': 'getting-started/introduction/#project-pages',
        'Mailinglists': 'getting-started/introduction/#mailing-lists',

        // Installation
        'Installation': 'getting-started/introduction/#installation',
        'Installationinstructions': 'getting-started/introduction/#installation',
        'Pythoninstallation': 'getting-started/introduction/#python-installation',
        'InstallingRobotFramework': 'getting-started/introduction/#installing-robot-framework',
        'Installingfromsource': 'getting-started/introduction/#installing-from-source',
        'Verifyinginstallation': 'getting-started/introduction/#verifying-installation',
        'Virtualenvironments': 'getting-started/introduction/#virtual-environments',

        // Demonstration
        'Demonstration': 'getting-started/demonstration/',
        'Ademonstration': 'getting-started/demonstration/',

        // === CREATING TEST DATA ===
        // Test Data Syntax
        'Testdatasyntax': 'creating-test-data/test-data-syntax/',
        'TestDataSyntax': 'creating-test-data/test-data-syntax/',
        'Filesanddirectories': 'creating-test-data/test-data-syntax/#files-and-directories',
        'Testdatasections': 'creating-test-data/test-data-syntax/#test-data-sections',
        'Testdatatables': 'creating-test-data/test-data-syntax/#test-data-sections',
        'Supportedfileformats': 'creating-test-data/test-data-syntax/#supported-file-formats',
        'Spaceseparatedformat': 'creating-test-data/test-data-syntax/#space-separated-format',
        'Pipeseparatedformat': 'creating-test-data/test-data-syntax/#pipe-separated-format',
        'reStructuredTextformat': 'creating-test-data/test-data-syntax/#restructuredtext-format',
        'JSONformat': 'creating-test-data/test-data-syntax/#json-format',
        'Rulesforparsingthedata': 'creating-test-data/test-data-syntax/#rules-for-parsing-the-data',
        'Ignoreddata': 'creating-test-data/test-data-syntax/#ignored-data',
        'Escaping': 'creating-test-data/test-data-syntax/#escaping',
        'Escapingspecialcharacters': 'creating-test-data/test-data-syntax/#escaping-special-characters',
        'Formingescapesequences': 'creating-test-data/test-data-syntax/#forming-escape-sequences',
        'Handlingemptyvalues': 'creating-test-data/test-data-syntax/#handling-empty-values',
        'Handlingspaces': 'creating-test-data/test-data-syntax/#handling-spaces',
        'Dividingdatatoseveralrows': 'creating-test-data/test-data-syntax/#dividing-data-to-several-rows',
        'Localization': 'creating-test-data/test-data-syntax/#localization',
        'Enablinglanguages': 'creating-test-data/test-data-syntax/#enabling-languages',
        'Built-inlanguages': 'creating-test-data/test-data-syntax/#built-in-languages',
        'Customlanguagefiles': 'creating-test-data/test-data-syntax/#custom-language-files',
        'Contributingtranslations': 'creating-test-data/test-data-syntax/#contributing-translations',
        'Style': 'creating-test-data/test-data-syntax/#style',

        // Creating Test Cases
        'Creatingtestcases': 'creating-test-data/creating-test-cases/',
        'CreatingTestCases': 'creating-test-data/creating-test-cases/',
        'Creatingtests': 'creating-test-data/creating-test-cases/',
        'Testcasesyntax': 'creating-test-data/creating-test-cases/#test-case-syntax',
        'Basicsyntax': 'creating-test-data/creating-test-cases/#basic-syntax',
        'SettingsintheTestCasesection': 'creating-test-data/creating-test-cases/#settings-in-the-test-case-section',
        'TestcaserelatedsettingsintheSettingsection': 'creating-test-data/creating-test-cases/#test-case-related-settings',
        'Usingarguments': 'creating-test-data/creating-test-cases/#using-arguments',
        'Positionalarguments': 'creating-test-data/creating-test-cases/#positional-arguments',
        'Defaultvalues': 'creating-test-data/creating-test-cases/#default-values',
        'Variablenumberofarguments': 'creating-test-data/creating-test-cases/#variable-number-of-arguments',
        'Namedarguments': 'creating-test-data/creating-test-cases/#named-arguments',
        'Namedargumentsyntax': 'creating-test-data/creating-test-cases/#named-arguments',
        'Freenamedarguments': 'creating-test-data/creating-test-cases/#free-named-arguments',
        'Named-onlyarguments': 'creating-test-data/creating-test-cases/#named-only-arguments',
        'Argumentsembeddedtokeywordnames': 'creating-test-data/creating-test-cases/#arguments-embedded-to-keyword-names',
        'Failures': 'creating-test-data/creating-test-cases/#failures',
        'Whentestcasefails': 'creating-test-data/creating-test-cases/#when-test-case-fails',
        'Errormessages': 'creating-test-data/creating-test-cases/#error-messages',
        'Testcasenameanddocumentation': 'creating-test-data/creating-test-cases/#test-case-name-and-documentation',
        'Taggingtestcases': 'creating-test-data/creating-test-cases/#tagging-test-cases',
        'Reservedtags': 'creating-test-data/creating-test-cases/#reserved-tags',
        'Testsetupandteardown': 'creating-test-data/creating-test-cases/#test-setup-and-teardown',
        'Testtemplates': 'creating-test-data/creating-test-cases/#test-templates',
        'Templateswithmultipleiterations': 'creating-test-data/creating-test-cases/#templates-with-multiple-iterations',
        'Templateswithembeddedarguments': 'creating-test-data/creating-test-cases/#templates-with-embedded-arguments',
        'Differenttestcasestyles': 'creating-test-data/creating-test-cases/#different-test-case-styles',
        'Keyword-drivenstyle': 'creating-test-data/creating-test-cases/#keyword-driven-style',
        'Data-drivenstyle': 'creating-test-data/creating-test-cases/#data-driven-style',
        'Behavior-drivenstyle': 'creating-test-data/creating-test-cases/#behavior-driven-style',

        // Creating Tasks (RPA)
        'Creatingtasks': 'creating-test-data/creating-tasks/',
        'rpa': 'creating-test-data/creating-tasks/',
        'Taskexecution': 'executing-tests/task-execution/',

        // Creating Test Suites
        'Creatingtestsuites': 'creating-test-data/creating-test-suites/',
        'Suitefiles': 'creating-test-data/creating-test-suites/#suite-files',
        'Suitedirectories': 'creating-test-data/creating-test-suites/#suite-directories',
        'Suiteinitializationfiles': 'creating-test-data/creating-test-suites/#suite-initialization-files',
        'Suitename': 'creating-test-data/creating-test-suites/#suite-name',
        'Suitedocumentation': 'creating-test-data/creating-test-suites/#suite-documentation',
        'Freesuitemetadata': 'creating-test-data/creating-test-suites/#free-suite-metadata',
        'Suitesetupandteardown': 'creating-test-data/creating-test-suites/#suite-setup-and-teardown',

        // Using Test Libraries
        'Usingtestlibraries': 'creating-test-data/using-test-libraries/',
        'Importinglibraries': 'creating-test-data/using-test-libraries/#importing-libraries',
        'Specifyinglibrarytoimpor': 'creating-test-data/using-test-libraries/#specifying-library-to-import',
        'Settingcustomnametolibrary': 'creating-test-data/using-test-libraries/#setting-custom-name-to-library',
        'Standardlibraries': 'creating-test-data/using-test-libraries/#standard-libraries',
        'Externallibraries': 'creating-test-data/using-test-libraries/#external-libraries',

        // Variables
        'Variables': 'creating-test-data/variables/',
        'Scalarvariables': 'creating-test-data/variables/#scalar-variables',
        'Listvariables': 'creating-test-data/variables/#list-variables',
        'Dictionaryvariables': 'creating-test-data/variables/#dictionary-variables',
        'Environmentvariables': 'creating-test-data/variables/#environment-variables',
        'Creatingvariables': 'creating-test-data/variables/#creating-variables',
        'Variablesection': 'creating-test-data/variables/#variable-section',
        'Variabletable': 'creating-test-data/variables/#variable-section',
        'Variablefilekeyword': 'creating-test-data/variables/#set-test-suite-global-variable',
        'Returnvaluesfromkeywords': 'creating-test-data/variables/#return-values-from-keywords',
        'Commandlinevariables': 'creating-test-data/variables/#command-line-variables',
        'Built-invariables': 'creating-test-data/variables/#built-in-variables',
        'Automaticvariables': 'creating-test-data/variables/#automatic-variables',
        'Operatingsystemvariables': 'creating-test-data/variables/#operating-system-variables',
        'Numbervariables': 'creating-test-data/variables/#number-variables',
        'Booleanandnone': 'creating-test-data/variables/#boolean-and-none',
        'Spaceandemptyvariables': 'creating-test-data/variables/#space-and-empty-variables',
        'Advancedvariablefeatures': 'creating-test-data/variables/#advanced-variable-features',
        'Extendedvariablesyntax': 'creating-test-data/variables/#extended-variable-syntax',
        'Assigningvariables': 'creating-test-data/variables/#assigning-variables',
        'InlinePythonevaluation': 'creating-test-data/variables/#inline-python-evaluation',

        // Creating User Keywords
        'Creatinguserkeywords': 'creating-test-data/creating-user-keywords/',
        'Userkeywordsyntax': 'creating-test-data/creating-user-keywords/#user-keyword-syntax',
        'Settingsinthekeywordsection': 'creating-test-data/creating-user-keywords/#settings-in-keyword-section',
        'Userkeywordname': 'creating-test-data/creating-user-keywords/#user-keyword-name',
        'Userkeyworddocumentation': 'creating-test-data/creating-user-keywords/#user-keyword-documentation',
        'Userkeywordtags': 'creating-test-data/creating-user-keywords/#user-keyword-tags',
        'Userkeywordarguments': 'creating-test-data/creating-user-keywords/#user-keyword-arguments',
        'Positional-onlyarguments': 'creating-test-data/creating-user-keywords/#positional-only-arguments',
        'Freenamedargumentswithuserkeywords': 'creating-test-data/creating-user-keywords/#free-named-arguments-with-user-keywords',
        'Named-onlyargumentswithuserkeywords': 'creating-test-data/creating-user-keywords/#named-only-arguments-with-user-keywords',
        'Embeddingargumentsintokeywordname': 'creating-test-data/creating-user-keywords/#embedding-arguments-into-keyword-name',
        'Embeddedargumentsyntax': 'creating-test-data/creating-user-keywords/#embedding-arguments-into-keyword-name',
        'Userkeywordreturnvalues': 'creating-test-data/creating-user-keywords/#user-keyword-return-values',
        'RETURN': 'creating-test-data/creating-user-keywords/#return-statement',
        'Userkeywordteardown': 'creating-test-data/creating-user-keywords/#user-keyword-teardown',
        'Userkeywordtimeout': 'creating-test-data/creating-user-keywords/#user-keyword-timeout',
        'Privateuserkeywords': 'creating-test-data/creating-user-keywords/#private-user-keywords',

        // Control Structures
        'Controlstructures': 'creating-test-data/control-structures/',
        'FORloops': 'creating-test-data/control-structures/#for-loops',
        'for': 'creating-test-data/control-structures/#for-loops',
        'forloop': 'creating-test-data/control-structures/#for-loops',
        'WHILEloops': 'creating-test-data/control-structures/#while-loops',
        'WHILE': 'creating-test-data/control-structures/#while-loops',
        'IF/ELSEstructures': 'creating-test-data/control-structures/#if-else-structures',
        'if': 'creating-test-data/control-structures/#if-else-structures',
        'ifelse': 'creating-test-data/control-structures/#if-else-structures',
        'TRY/EXCEPT': 'creating-test-data/control-structures/#try-except',
        'tryexcept': 'creating-test-data/control-structures/#try-except',
        'BREAK': 'creating-test-data/control-structures/#break-and-continue',
        'CONTINUE': 'creating-test-data/control-structures/#break-and-continue',
        'InlineIF': 'creating-test-data/control-structures/#inline-if',
        'inlineif': 'creating-test-data/control-structures/#inline-if',

        // Resource and Variable Files
        'Resourceandvariablefiles': 'creating-test-data/resource-and-variable-files/',
        'Resourcefiles': 'creating-test-data/resource-and-variable-files/#resource-files',
        'Takingresourcefilesintouse': 'creating-test-data/resource-and-variable-files/#taking-resource-files-into-use',
        'Resourcefilesyntax': 'creating-test-data/resource-and-variable-files/#resource-file-syntax',
        'Variablefiles': 'creating-test-data/resource-and-variable-files/#variable-files',
        'Takingvariablefilesintouse': 'creating-test-data/resource-and-variable-files/#taking-variable-files-into-use',
        'Creatingvariablefiles': 'creating-test-data/resource-and-variable-files/#creating-variable-files',

        // Advanced Features
        'Advancedfeatures': 'creating-test-data/advanced-features/',
        'Handlingenvironmentandsystemvariables': 'creating-test-data/advanced-features/',
        'Librarysearchorder': 'creating-test-data/advanced-features/#library-search-order',
        'Keywordshadowingwarnings': 'creating-test-data/advanced-features/#keyword-shadowing-warnings',
        'Timeouts': 'creating-test-data/advanced-features/#timeouts',
        'Testcasetimeout': 'creating-test-data/advanced-features/#test-case-timeout',
        'Continuingonfailure': 'creating-test-data/advanced-features/#continuing-on-failure',

        // === EXECUTING TEST CASES ===
        // Basic Usage
        'Basicusage': 'executing-tests/basic-usage/',
        'Executingtestcases': 'executing-tests/basic-usage/',
        'executingtestcases': 'executing-tests/basic-usage/',
        'Startingtestexecution': 'executing-tests/basic-usage/#starting-test-execution',
        'Specifyingtestdatatobeexecuted': 'executing-tests/basic-usage/#specifying-test-data',
        'Usingcommandlineoptions': 'executing-tests/basic-usage/#using-command-line-options',
        'Usingoptions': 'executing-tests/basic-usage/#using-options',
        'Shortandlongoptions': 'executing-tests/basic-usage/#short-and-long-options',
        'Settingoptionvalues': 'executing-tests/basic-usage/#setting-option-values',
        'Disablingoptionsacceptingnovalues': 'executing-tests/basic-usage/#disabling-options',
        'Simplepatterns': 'executing-tests/basic-usage/#simple-patterns',
        'wildcards': 'executing-tests/basic-usage/#simple-patterns',
        'Tagpatterns': 'executing-tests/basic-usage/#tag-patterns',
        'Testresults': 'executing-tests/basic-usage/#test-results',
        'Commandlineoutput': 'executing-tests/basic-usage/#command-line-output',
        'Generatedoutputfiles': 'executing-tests/basic-usage/#generated-output-files',
        'Returncodes': 'executing-tests/basic-usage/#return-codes',
        'Errorsandwarningsduringexecution': 'executing-tests/basic-usage/#errors-and-warnings',
        'Argumentfiles': 'executing-tests/basic-usage/#argument-files',
        'Gettinghelpandversioninformation': 'executing-tests/basic-usage/#getting-help',
        'Creatingstart-upscripts': 'executing-tests/basic-usage/#creating-start-up-scripts',
        'start-upscript': 'executing-tests/basic-usage/#creating-start-up-scripts',
        'start-upscripts': 'executing-tests/basic-usage/#creating-start-up-scripts',
        'Debuggingproblems': 'executing-tests/basic-usage/#debugging-problems',

        // Test Execution
        'Testexecution': 'executing-tests/test-execution/',
        'Executionflow': 'executing-tests/test-execution/#execution-flow',
        'Setups': 'executing-tests/test-execution/#setups',
        'Teardowns': 'executing-tests/test-execution/#teardowns',
        'Suitestatus': 'executing-tests/test-execution/#suite-status',
        'Teststatus': 'executing-tests/test-execution/#test-status',
        'Continueononfailure': 'executing-tests/test-execution/#continue-on-failure',
        'Continueonfailure': 'executing-tests/test-execution/#continue-on-failure',
        'Skippingtests': 'executing-tests/test-execution/#skipping-tests',
        'skipped': 'executing-tests/test-execution/#skipping-tests',
        'Stoppingexecution': 'executing-tests/test-execution/#stopping-execution',
        'Stoppingtestexecutiongracefully': 'executing-tests/test-execution/#stopping-gracefully',

        // Task Execution
        'executingtasks': 'executing-tests/task-execution/',

        // Post-processing Outputs
        'Post-processingoutputs': 'executing-tests/post-processing/',
        'UsingRebot': 'executing-tests/post-processing/#using-rebot',
        'rebot': 'executing-tests/post-processing/#using-rebot',
        'Combiningoutputs': 'executing-tests/post-processing/#combining-outputs',
        'Mergingoutputs': 'executing-tests/post-processing/#merging-outputs',

        // Configuring Execution
        'Configuringexecution': 'executing-tests/configuring-execution/',
        'Selectingtestcases': 'executing-tests/configuring-execution/#selecting-test-cases',
        'Bytestnames': 'executing-tests/configuring-execution/#by-test-names',
        'Bysuitenames': 'executing-tests/configuring-execution/#by-suite-names',
        'Bytagnames': 'executing-tests/configuring-execution/#by-tag-names',
        'Re-executingfailedtestcases': 'executing-tests/configuring-execution/#re-executing-failed-tests',
        'Settingsuitename': 'executing-tests/configuring-execution/#setting-suite-name',
        'Settingsuitedocumentation': 'executing-tests/configuring-execution/#setting-suite-documentation',
        'Settingfreesuitemetadata': 'executing-tests/configuring-execution/#setting-free-suite-metadata',
        'Settingtesttags': 'executing-tests/configuring-execution/#setting-test-tags',
        'Selectingfilestoparse': 'executing-tests/configuring-execution/#selecting-files-to-parse',
        'Randomizingexecutionorder': 'executing-tests/configuring-execution/#randomizing-execution-order',
        'Controllingconsoleoutput': 'executing-tests/configuring-execution/#controlling-console-output',
        'Settinglisteners': 'executing-tests/configuring-execution/#setting-listeners',
        'Modulesearchpath': 'executing-tests/configuring-execution/#module-search-path',
        'Pre-runmodifier': 'executing-tests/configuring-execution/#pre-run-modifier',
        'pre-runmodifier': 'executing-tests/configuring-execution/#pre-run-modifier',
        'pre-runmodifiers': 'executing-tests/configuring-execution/#pre-run-modifier',
        'Dryrun': 'executing-tests/configuring-execution/#dry-run',

        // Output Files
        'Outputfiles': 'executing-tests/output-files/',
        'Differentoutputfiles': 'executing-tests/output-files/#different-output-files',
        'Outputfile': 'executing-tests/output-files/#output-file',
        'output.xml': 'executing-tests/output-files/#output-file',
        'Logfile': 'executing-tests/output-files/#log-file',
        'Reportfile': 'executing-tests/output-files/#report-file',
        'XUnitcompatibleresultfile': 'executing-tests/output-files/#xunit-file',
        'xunit': 'executing-tests/output-files/#xunit-file',
        'xunitfile': 'executing-tests/output-files/#xunit-file',
        'Debugfile': 'executing-tests/output-files/#debug-file',
        'Timestampingoutputfiles': 'executing-tests/output-files/#timestamping-output-files',
        'Settingtitles': 'executing-tests/output-files/#setting-titles',
        'Settingbackgroundcolors': 'executing-tests/output-files/#setting-background-colors',
        'Loglevels': 'executing-tests/output-files/#log-levels',
        'Settingloglevel': 'executing-tests/output-files/#setting-log-level',
        'Splittinglogs': 'executing-tests/output-files/#splitting-logs',
        'Configuringstatistics': 'executing-tests/output-files/#configuring-statistics',
        'Removingandflatteningkeywords': 'executing-tests/output-files/#removing-keywords',
        'Automaticallyexpandingkeywords': 'executing-tests/output-files/#expanding-keywords',
        'Systemlog': 'executing-tests/output-files/#system-log',
        'Pre-Rebotmodifier': 'executing-tests/output-files/#pre-rebot-modifier',
        'pre-Rebotmodifier': 'executing-tests/output-files/#pre-rebot-modifier',

        // === EXTENDING ROBOT FRAMEWORK ===
        // Creating Test Libraries
        'Creatingtestlibraries': 'extending/creating-test-libraries/',
        'Supportedprogramminglanguages': 'extending/creating-test-libraries/#supported-programming-languages',
        'Differenttestlibraryapis': 'extending/creating-test-libraries/#different-test-library-apis',
        'Creatingtestlibryclassormodule': 'extending/creating-test-libraries/#creating-test-library-class',
        'Libraryname': 'extending/creating-test-libraries/#library-name',
        'Providingargumentstolibraries': 'extending/creating-test-libraries/#providing-arguments-to-libraries',
        'Libraryscope': 'extending/creating-test-libraries/#library-scope',
        'Libraryversion': 'extending/creating-test-libraries/#library-version',
        'Specifyingdocumentationformat': 'extending/creating-test-libraries/#documentation-format',
        'Libraryactingaslistener': 'extending/creating-test-libraries/#library-acting-as-listener',
        'librarydecorator': 'extending/creating-test-libraries/#library-decorator',
        'Creatingkeywords': 'extending/creating-test-libraries/#creating-keywords',
        'Keywordnames': 'extending/creating-test-libraries/#keyword-names',
        'keyworddecorator': 'extending/creating-test-libraries/#keyword-decorator',
        'Keywordarguments': 'extending/creating-test-libraries/#keyword-arguments',
        'Freekeywordarguments': 'extending/creating-test-libraries/#free-keyword-arguments',
        'Keyword-onlyarguments': 'extending/creating-test-libraries/#keyword-only-arguments',
        'Positional-onlyargumentsinlibraries': 'extending/creating-test-libraries/#positional-only-arguments',
        'Embeddingargumentsintokeywordnames': 'extending/creating-test-libraries/#embedding-arguments',
        'Asynchronouskeywords': 'extending/creating-test-libraries/#asynchronous-keywords',
        'Argumenttypes': 'extending/creating-test-libraries/#argument-types',
        'Supportedconversions': 'extending/creating-test-libraries/#supported-conversions',
        'Specifyingargumenttypes': 'extending/creating-test-libraries/#specifying-argument-types',
        'Customargumentconverters': 'extending/creating-test-libraries/#custom-argument-converters',
        'Reportingkeywordstatus': 'extending/creating-test-libraries/#reporting-keyword-status',
        'Logginginformation': 'extending/creating-test-libraries/#logging-information',
        'Errorsandwarnings': 'extending/creating-test-libraries/#errors-and-warnings',
        'HTMLinerrormessages': 'extending/creating-test-libraries/#html-in-error-messages',
        'Returningvalues': 'extending/creating-test-libraries/#returning-values',
        'CommunicatingwithRobotFramework': 'extending/creating-test-libraries/#communicating-with-robot-framework',
        'Documentinglibraries': 'extending/creating-test-libraries/#documenting-libraries',
        'Dynamiclibraryapi': 'extending/creating-test-libraries/#dynamic-library-api',
        'Dynamiclibrary': 'extending/creating-test-libraries/#dynamic-library-api',
        'Gettingdynamickeywordnames': 'extending/creating-test-libraries/#getting-dynamic-keyword-names',
        'Runningdynamickeywords': 'extending/creating-test-libraries/#running-dynamic-keywords',
        'Hybridlibraryapi': 'extending/creating-test-libraries/#hybrid-library-api',
        'Extendingexistinglibraries': 'extending/creating-test-libraries/#extending-existing-libraries',

        // Remote Library Interface
        'Remotelibrary': 'extending/remote-library/',
        'Remotelibaryinterface': 'extending/remote-library/',
        'Takingremotelibraryintouse': 'extending/remote-library/#taking-remote-library-into-use',
        'Supportedargumentandreturntypes': 'extending/remote-library/#supported-argument-types',
        'Remoteprotocol': 'extending/remote-library/#remote-protocol',

        // Listener Interface
        'Listenerinterface': 'extending/listener-interface/',
        'listenerinterface': 'extending/listener-interface/',
        'Listenerstructure': 'extending/listener-interface/#listener-structure',
        'Listenerinterfaceversions': 'extending/listener-interface/#listener-interface-versions',
        'Listenerversion2': 'extending/listener-interface/#listener-version-2',
        'Listenerversion3': 'extending/listener-interface/#listener-version-3',
        'Takinglistenersintouse': 'extending/listener-interface/#taking-listeners-into-use',
        'Registeringlistenersfromcommandline': 'extending/listener-interface/#registering-listeners',
        'Librariesaslisteners': 'extending/listener-interface/#libraries-as-listeners',
        'librarylisteners': 'extending/listener-interface/#libraries-as-listeners',
        'Listenerexamples': 'extending/listener-interface/#listener-examples',
        'Modifyingdataandresults': 'extending/listener-interface/#modifying-data-and-results',

        // Parser Interface
        'Parserinterface': 'extending/parser-interface/',
        'Takingcustomparsersintouse': 'extending/parser-interface/#taking-custom-parsers-into-use',
        'Parserinterface2': 'extending/parser-interface/#parser-interface',
        'Parsedmodel': 'extending/parser-interface/#parsed-model',
        'Parserexamples': 'extending/parser-interface/#parser-examples',

        // === SUPPORTING TOOLS ===
        // Libdoc
        'Libdoc': 'supporting-tools/libdoc/',
        'libdoc': 'supporting-tools/libdoc/',
        'Libdocgeneral': 'supporting-tools/libdoc/',
        'UsingLibdoc': 'supporting-tools/libdoc/#using-libdoc',
        'Libdocoutputformats': 'supporting-tools/libdoc/#libdoc-output-formats',
        'Viewinglibrarydocumentation': 'supporting-tools/libdoc/#viewing-library-documentation',
        'Hotkeys': 'supporting-tools/libdoc/#hotkeys',
        'Internallinking': 'supporting-tools/libdoc/#internal-linking',
        'internallinking': 'supporting-tools/libdoc/#internal-linking',

        // Testdoc
        'Testdoc': 'supporting-tools/testdoc/',
        'testdoc': 'supporting-tools/testdoc/',
        'UsingTestdoc': 'supporting-tools/testdoc/#using-testdoc',

        // Tidy
        'Tidy': 'supporting-tools/tidy/',
        'tidy': 'supporting-tools/tidy/',

        // Other Tools
        'Othertools': 'supporting-tools/other-tools/',
        'Testrunnertools': 'supporting-tools/other-tools/#test-runners',
        'Testdataeditors': 'supporting-tools/other-tools/#test-data-editors',
        'Buildtools': 'supporting-tools/other-tools/#build-tools',

        // === APPENDICES ===
        'Appendices': 'appendices/',
        'Availablesettings': 'appendices/available-settings/',
        'settings': 'appendices/available-settings/',
        'Settingsinthedatasection': 'appendices/available-settings/#settings-in-data-section',
        'Settingsintheinitialization': 'appendices/available-settings/#settings-in-initialization-files',

        // Command Line Options
        'Commandlineoptions': 'appendices/command-line-options/',
        'Allcommandlineoptions': 'appendices/command-line-options/',
        'Commandlineoptionsforexecuting': 'appendices/command-line-options/#robot-options',
        'Commandlineoptionsforpostprocessing': 'appendices/command-line-options/#rebot-options',

        // Translations
        'Translations': 'appendices/translations/',

        // Documentation Formatting
        'Documentationformatting': 'appendices/documentation-formatting/',
        'Documentationsyntax': 'appendices/documentation-formatting/',
        'HTMLformatting': 'appendices/documentation-formatting/#html-formatting',
        'Representingnewlines': 'appendices/documentation-formatting/#newlines',
        'Internallinks': 'appendices/documentation-formatting/#internal-links',

        // Time Formats
        'Timeformat': 'appendices/time-format/',
        'Timeformats': 'appendices/time-format/',

        // Boolean Arguments
        'Booleanarguments': 'appendices/boolean-arguments/',

        // Evaluating Expressions
        'Evaluatingexpressions': 'appendices/evaluating-expressions/'
    };

    /**
     * Get the base URL for the site (handles versioned docs)
     */
    function getBaseUrl() {
        const path = window.location.pathname;
        // Handle versioned docs pattern like /robotframework/7.0/
        const versionMatch = path.match(/^(\/robotframework\/[\d.]+\/)/);
        if (versionMatch) {
            return versionMatch[1];
        }
        // Handle /robotframework/latest/
        const latestMatch = path.match(/^(\/robotframework\/latest\/)/);
        if (latestMatch) {
            return latestMatch[1];
        }
        // Default - just get to root
        return path.replace(/[^\/]*$/, '');
    }

    /**
     * Handle legacy anchor redirect
     */
    function handleLegacyAnchor() {
        const hash = window.location.hash;

        // Only process if there's a hash
        if (!hash || hash.length <= 1) {
            return;
        }

        const anchor = hash.substring(1); // Remove the '#'

        // Check if this is a legacy anchor that needs redirecting
        if (LEGACY_ANCHOR_MAP.hasOwnProperty(anchor)) {
            const newPath = LEGACY_ANCHOR_MAP[anchor];
            const baseUrl = getBaseUrl();
            const newUrl = baseUrl + newPath;

            console.log('[Legacy Redirect] Redirecting from #' + anchor + ' to ' + newUrl);

            // Use replace to avoid adding to browser history
            window.location.replace(newUrl);
        }
    }

    // Run on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', handleLegacyAnchor);
    } else {
        handleLegacyAnchor();
    }

    // Also handle hash changes (for SPA navigation)
    window.addEventListener('hashchange', handleLegacyAnchor);
})();
