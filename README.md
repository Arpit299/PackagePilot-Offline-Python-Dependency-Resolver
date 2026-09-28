# PackagePilot — Offline Python Dependency Resolver

PackagePilot is an offline Python dependency resolution engine that models package relationships, evaluates version constraints, detects dependency conflicts, and calculates a compatible installation or update plan without requiring access to an online package repository.

The project is implemented as a standalone Python application using the standard library and focuses on dependency graphs, semantic versioning, constraint solving, and backtracking.

## Features

* Offline dependency resolution
* Semantic version parsing
* Version comparison
* Compound version constraints
* Dependency graph construction
* Dependency conflict detection
* Backtracking-based resolution
* Constraint propagation
* Installed-version awareness
* Installation planning
* Upgrade planning
* Downgrade detection
* Package removal detection
* JSON package-index support
* Requirements-file support
* Installed-package state support
* JSON resolution reports
* Command-line interface
* Built-in self-test
* No external Python dependencies

## Tech Stack

**Python | Data Structures & Algorithms | Dependency Graphs | Semantic Versioning | Constraint Solving | JSON | CLI**

## DSA Used

PackagePilot uses several core data structures and algorithms:

* **Hash Maps** for package and version indexing
* **Graphs** for dependency relationships
* **Sets** for visited packages and conflict tracking
* **Sorting** for candidate version ordering
* **Backtracking** for exploring compatible dependency combinations
* **Constraint Propagation** for narrowing valid versions
* **Recursive Graph Traversal** for resolving transitive dependencies

## Architecture

```text
Package Index
      ↓
Requirement Parser
      ↓
Version Constraint Engine
      ↓
Dependency Graph
      ↓
Candidate Version Selection
      ↓
Constraint Propagation
      ↓
Backtracking Resolver
      ↓
Conflict Detection
      ↓
Resolution Plan
      ↓
JSON Report
```

## Example Dependency Graph

```text
Application
├── Alpha >=1.0,<2.0
│   ├── Beta >=1.0,<2.0
│   └── Gamma >=2.0
└── Delta >=2.0
```

PackagePilot recursively resolves the complete dependency graph rather than checking only direct requirements.

## Supported Constraints

PackagePilot supports common version operators such as:

```text
==1.5.0
>=1.0.0
<=2.0.0
>1.2.0
<3.0.0
!=1.8.0
```

Compound constraints are also supported:

```text
>=1.0,<2.0
>=2.0,!=2.4.0
```

## Installation

PackagePilot uses only the Python standard library.

Clone the repository:

```bash
git clone https://github.com/Arpit299/packagepilot.git
cd packagepilot
```

No external packages are required.

## Run the Self-Test

```bash
python packagepilot.py
```

or:

```bash
python packagepilot.py --self-test
```

Example:

```text
PACKAGEPILOT SELF-TEST: PASS
Resolved: alpha==1.0.0, beta==1.5.0, delta==2.0.0, gamma==2.5.0
Search States: 5
```

## Package Index

Package metadata can be represented in JSON.

Example:

```json
{
  "alpha": {
    "1.0.0": {
      "dependencies": {
        "beta": ">=1.0,<2.0"
      }
    }
  },
  "beta": {
    "1.5.0": {
      "dependencies": {}
    }
  }
}
```

The resolver uses this information to construct the dependency graph and identify compatible versions.

## Requirements File

Example:

```text
alpha>=1.0,<2.0
beta>=1.0
gamma==2.5.0
```

PackagePilot parses the root requirements and recursively resolves all transitive dependencies.

## Installed Package State

An installed package state can also be supplied to determine whether packages should be kept, upgraded, downgraded, installed, or removed.

Example:

```json
{
  "alpha": "1.0.0",
  "beta": "1.2.0"
}
```

## Resolve Dependencies

Example:

```bash
python packagepilot.py resolve index.json requirements.txt --installed installed.json --output result.json
```

The resolver produces a structured result containing the selected package versions and the resulting installation plan.

## Resolution Process

```text
Root Requirements
        ↓
Select Candidate
        ↓
Read Dependencies
        ↓
Add Dependencies to Graph
        ↓
Apply Version Constraints
        ↓
Detect Conflicts
        ↓
Backtrack When Required
        ↓
Select Compatible Versions
        ↓
Generate Plan
```

## Conflict Detection

PackagePilot can identify incompatible requirements such as:

```text
Package A requires beta>=2.0
Package B requires beta<2.0
```

The resolver marks the dependency set as unsatisfiable instead of silently selecting an incompatible version.

## Installation Planning

Once a compatible dependency graph is found, PackagePilot compares it with the installed state.

Example:

```text
alpha 1.0.0 → KEEP
beta 1.2.0 → UPGRADE
gamma       → INSTALL
delta 2.1.0 → DOWNGRADE
oldpkg      → REMOVE
```

This makes the system behave more like a dependency-management engine instead of a simple version checker.

## Project Structure

```text
packagepilot/
├── packagepilot.py
├── README.md
├── index.json
├── requirements.txt
├── installed.json
└── result.json
```

## Example Workflow

```text
Package Metadata
      ↓
Requirement Parsing
      ↓
Version Evaluation
      ↓
Dependency Graph
      ↓
Conflict Detection
      ↓
Backtracking Search
      ↓
Compatible Resolution
      ↓
Installation Plan
```

## Performance

PackagePilot avoids blindly scanning every possible dependency state.

Its resolver uses:

* Candidate ordering
* Constraint filtering
* Hash-based package lookup
* Dependency indexing
* Early conflict detection
* Backtracking only when necessary

This reduces unnecessary search across the dependency space.

## Use Cases

PackagePilot can be used for:

* Dependency-resolution experiments
* Package-management research
* Version-conflict analysis
* Build-system prototyping
* Software dependency graph analysis
* Offline package planning
* Dependency-aware update simulations
* DSA and algorithm demonstrations

## Limitations

PackagePilot is an offline dependency-resolution engine and does not directly download or install packages from PyPI.

It does not attempt to reproduce every feature of production package managers such as pip, Poetry, uv, or conda.

Its primary purpose is to demonstrate the algorithms and data structures behind dependency resolution.

## Future Improvements

Potential extensions include:

* PyPI metadata ingestion
* Wheel compatibility analysis
* Python-version constraints
* Platform-specific dependencies
* Dependency lockfiles
* SAT/SMT-based resolution
* Parallel candidate evaluation
* Constraint caching
* Resolution explanations
* Interactive dependency graphs
* FastAPI service interface
* Dockerized package-resolution service

