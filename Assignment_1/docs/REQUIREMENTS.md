# Assignment I requirements

## Application and architecture

| #   | Requirement                                                                                   | Stage |
| --- | --------------------------------------------------------------------------------------------- | ----- |
| R1  | Small functional application in Python, with synthetic data and seeded accounts               | 2, 3  |
| R2  | Identify functional and non-functional requirements and map the data flow before implementing | 1     |
| R3  | Three components running as separate processes (containers), talking over HTTP.               | 2     |
| R4  | Each component has different responsibilities and permissions                                 | 1, 2  |
| R5  | At least three functionalities, one of them using all three components                        | 3     |
| R6  | One small helper package of my own                                                            | 2     |
| R7  | CLI client as the user interface                                                              | 3     |

## Authentication and authorization

| #   | Requirement                                                                                      | Stage   |
| --- | ------------------------------------------------------------------------------------------------ | ------- |
| R8  | Authentication and authorization enforcement                                                     | 3       |
| R9  | Two roles: one ordinary, one privileged with a restricted action                                 | 3       |
| R10 | Seed at least two ordinary users and one privileged user                                         | 3       |
| R11 | Explain how tokens bind authority to service, resource, action and validity period               | 1, 9    |
| R12 | Apply three course design principles, each with a design decision, its implementation and a test | 1, 3, 9 |

## Vulnerabilities

| #   | Requirement                                                      | Stage |
| --- | ---------------------------------------------------------------- | ----- |
| R13 | Plant three vulnerabilities from the course CWE catalog          | 4     |
| R14 | Plant one vulnerability that comes from composing the components | 4     |
| R15 | Document all four in the report                                  | 8, 9  |
| R16 | Correct confirmed violations of the security guarantees          | 6     |

## SSDLC and CI/CD

| #   | Requirement                                                                                                        | Stage |
| --- | ------------------------------------------------------------------------------------------------------------------ | ----- |
| R17 | Commit a plan covering the four phases before feature code, using asset, threat, control, activity, evidence, gate | 1     |
| R18 | Jenkins pipeline on every push and pull request                                                                    | 5     |
| R19 | Pipeline builds the components and runs static and dependency analysis                                             | 5     |
| R20 | Pipeline starts a fresh environment and runs functional and authorization tests                                    | 5     |
| R21 | Pipeline saves test and analysis results as artifacts                                                              | 5     |
| R22 | Define which findings block a release and make the pipeline fail on them                                           | 5     |

## Submission

| #   | Requirement                                                         | Stage  |
| --- | ------------------------------------------------------------------- | ------ |
| R23 | README with purpose and exact commands to build, seed, run and test | 8      |
| R24 | Initial plan and full git history kept                              | 1 to 9 |
| R25 | Architecture description, threat model, access-control matrix       | 1, 8   |
| R26 | Jenkinsfile and the helper package in the repo                      | 2, 5   |
| R27 | Report of about 2,000 to 2,500 words                                | 9      |
| R28 | AI-use declaration following https://studerende.au.dk/en/gai        | 9      |

## Optional

| #   | Requirement                                                                                                                                                                 | Stage |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| O1  | Supply-chain attack: benign and malicious version of the helper package, malicious code enters through installation                                                         | 7     |
| O2  | Experiment A: consumer-owned manifest with name, source, version and SHA-256; swapped bytes are blocked at install                                                          | 7     |
| O3  | Experiment B: approve the malicious version on a separate branch, record what it can reach, contain it with authorization or isolation, and show the benign job still works | 7     |
| O4  | Report section on where the malicious code entered and how it was contained                                                                                                 | 9     |
