# Assignment I requirements

## Application and architecture

| #   | Requirement                                                              | Stage |
| --- | ------------------------------------------------------------------------ | ----- |
| R1  | Small Python app with synthetic data and seeded accounts                 | 2, 3  |
| R2  | Functional/non-functional requirements and data flow before coding       | 1     |
| R3  | Three components as separate containers, talking HTTP                    | 2     |
| R4  | Each component has its own responsibilities and permissions              | 1, 2  |
| R5  | Three or more features, one going through all three components           | 3     |
| R6  | One small helper package of my own                                       | 2     |
| R7  | CLI client as the interface                                              | 3     |

## Authentication and authorization

| #   | Requirement                                                                         | Stage   |
| --- | ----------------------------------------------------------------------------------- | ------- |
| R8  | Enforced authentication and authorization                                           | 3       |
| R9  | Two roles: ordinary, and privileged with a restricted action                        | 3       |
| R10 | Seed two or more ordinary users and one privileged user                             | 3       |
| R11 | Explain how tokens bind authority to service, resource, action and validity period  | 1, 9    |
| R12 | Three course design principles, each with decision, code and test                   | 1, 3, 9 |

## Vulnerabilities

| #   | Requirement                                             | Stage |
| --- | ------------------------------------------------------- | ----- |
| R13 | Plant three vulnerabilities from the course CWE catalog | 4     |
| R14 | Plant one that comes from composing the components      | 4     |
| R15 | Document all four in the report                         | 8, 9  |
| R16 | Fix confirmed violations of the security guarantees     | 6     |

## SSDLC and CI/CD

| #   | Requirement                                                                                          | Stage |
| --- | ---------------------------------------------------------------------------------------------------- | ----- |
| R17 | Plan for the four phases committed before feature code (asset, threat, control, activity, evidence, gate) | 1     |
| R18 | Jenkins pipeline on every push and PR                                                                | 5     |
| R19 | Pipeline builds components, runs static and dependency analysis                                      | 5     |
| R20 | Pipeline starts a fresh environment, runs functional and authorization tests                         | 5     |
| R21 | Pipeline saves results as artifacts                                                                  | 5     |
| R22 | Define blocking findings and fail the pipeline on them                                               | 5     |

## Submission

| #   | Requirement                                                   | Stage  |
| --- | ------------------------------------------------------------- | ------ |
| R23 | README with purpose and exact build, seed, run, test commands  | 8      |
| R24 | Initial plan and full git history kept                        | 1 to 9 |
| R25 | Architecture, threat model, access-control matrix             | 1, 8   |
| R26 | Jenkinsfile and helper package in the repo                    | 2, 5   |
| R27 | Report, about 2,000 to 2,500 words                            | 9      |
| R28 | AI-use declaration per https://studerende.au.dk/en/gai        | 9      |

## Optional

| #   | Requirement                                                                                                         | Stage |
| --- | ------------------------------------------------------------------------------------------------------------------- | ----- |
| O1  | Supply-chain attack: benign and malicious helper versions, malicious code enters at install                         | 7     |
| O2  | Experiment A: consumer-owned manifest (name, source, version, SHA-256) blocks swapped bytes at install              | 7     |
| O3  | Experiment B: approve the malicious version on a branch, record its reach, contain it, show the benign job still works | 7     |
| O4  | Report section on where the malicious code entered and how it was contained                                         | 9     |
