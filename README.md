# AI-Powered Testing Agent

## Overview
This project demonstrates an intelligent software testing agent built using the **Model Context Protocol (MCP)**. The agent automatically generates, executes, and iterates on **JUnit test cases** for Java projects, aiming to maximize code coverage and improve software reliability.  

The project integrates AI-assisted development tools with traditional software engineering practices, including Maven, JaCoCo, and Git workflows.
 

---

## Features

- **Automated Test Generation**
  - Analyzes Java source code for class and method signatures.
  - Generates JUnit tests automatically.
  - Handles edge cases and improves coverage iteratively.

- **Coverage Analysis**
  - Parses JaCoCo reports to identify uncovered code.
  - Provides recommendations to improve test coverage.
  - Tracks test quality metrics over time.

- **Git Automation**
  - Tools for `status`, `add_all`, `commit`, `push`, and `pull_request`.
  - Automatically commits changes when coverage thresholds are met.
  - Supports CI/CD workflow integration.

- **Intelligent Test Iteration**
  - Automatic improvement of test cases based on coverage gaps.
  - Debugging and bug-fix suggestions for failed tests.
  - Autonomous commits for every coverage improvement.

- **Creative Extensions**
  - Specification-based testing with boundary value analysis and equivalence classes.

---

## Prerequisites

- **Python** 3.10+ with virtual environment support
- **Node.js** 18+ (LTS recommended)
- **Java** 11+ and **Maven** 3.6+
- **VS Code** with Chat view and MCP integration
- **Git** with active GitHub account

---

## Setup

1. Run server.py
2. Go to extensions and run the "Sanam Choudhary - MCP" server. Hover over the server and select "start"
3. Upload your Java project into the Sample Java Folder
4. In the chat, type "run #file:tester:prompt:md on <javaproject>" and the testing agent will analyze your code, create tests, examine jacoco reports, and provide feedback.



## Report
1. Please download the "vscode-pdf" extension to view the report pdf file in the "report" folder
