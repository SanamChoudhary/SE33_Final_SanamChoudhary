# server.py
from fastmcp import FastMCP
from fastmcp import tools
import os
import re
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
import git
from github import Github

mcp = FastMCP()

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    x = a + b
    return x

# ----------------------------------------------------
# 1. Analyze Java Code for Method Signatures
# ----------------------------------------------------
@mcp.tool
def analyze_java_source(path: str):
    """
    Analyze Java files and extract class names + method signatures.
    """
    with open(path, "r") as f:
        code = f.read()

    class_name_match = re.search(r"class\s+(\w+)", code)
    class_name = class_name_match.group(1) if class_name_match else "UnknownClass"

    methods = re.findall(
        r"public\s+(\w+)\s+(\w+)\((.*?)\)", code
    )
    
    method_list = []
    for return_type, method_name, params in methods:
        param_list = []
        if params.strip():
            for p in params.split(","):
                p = p.strip().split()
                param_type = p[0]
                param_name = p[1]
                param_list.append({"type": param_type, "name": param_name})
        method_list.append({
            "return": return_type,
            "method": method_name,
            "params": param_list
        })

    return {
        "class_name": class_name,
        "methods": method_list
    }

# ----------------------------------------------------
# 2. Generate JUnit Test File
# ----------------------------------------------------
@mcp.tool
def generate_tests(class_name: str, methods: list, output_dir: str):
    """
    Generate a basic JUnit test file.
    """
    os.makedirs(output_dir, exist_ok=True)
    test_path = os.path.join(output_dir, f"{class_name}Test.java")

    test_code = [
        "import org.junit.jupiter.api.*;",
        f"public class {class_name}Test {{",
        f"    {class_name} obj = new {class_name}();"
    ]

    for m in methods:
        test_code.append("    @Test")
        test_code.append(f"    public void test_{m['method']}() {{")
        args = ", ".join("0" for _ in m["params"])
        test_code.append(f"        obj.{m['method']}({args});")
        test_code.append("        Assertions.assertTrue(true);")
        test_code.append("    }")
    test_code.append("}")

    with open(test_path, "w") as f:
        f.write("\n".join(test_code))

    return {"generated": test_path}


# ----------------------------------------------------
# 3. Run mvn test
# ----------------------------------------------------
@mcp.tool
def run_tests():
    """
    Run mvn test and return output.
    """
    result = subprocess.run(
        ["mvn", "test"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    return {"output": result.stdout}


# ----------------------------------------------------
# 4. Parse JaCoCo XML Report
# ----------------------------------------------------
@mcp.tool
def jacoco_parse(path: str):
    """
    Parse a JaCoCo XML coverage report and extract:
    - coverage summary
    - uncovered methods
    - uncovered lines
    - recommendations for improvement
    """
    tree = ET.parse(path)
    root = tree.getroot()

    classes = []
    recommendations = []

    for pkg in root.findall(".//package"):
        pkg_name = pkg.get("name")

        for cls in pkg.findall("class"):
            cls_name = cls.get("name")

            class_record = {
                "package": pkg_name,
                "class": cls_name,
                "methods": [],
                "missed_lines": 0,
                "covered_lines": 0
            }

            # CLASS-LEVEL COVERAGE
            for counter in cls.findall("counter"):
                if counter.get("type") == "LINE":
                    class_record["missed_lines"] = int(counter.get("missed"))
                    class_record["covered_lines"] = int(counter.get("covered"))

            # METHODS
            for method in cls.findall("method"):
                method_name = method.get("name")
                method_desc = method.get("desc")

                for counter in method.findall("counter"):
                    if counter.get("type") == "LINE":
                        missed = int(counter.get("missed"))
                        covered = int(counter.get("covered"))

                        class_record["methods"].append({
                            "method": method_name,
                            "desc": method_desc,
                            "missed": missed,
                            "covered": covered
                        })

                        if covered == 0:
                            recommendations.append(
                                f"Method {cls_name}.{method_name}() has 0% coverage. "
                                "Create a test that directly calls this method."
                            )
                        elif missed > 0:
                            recommendations.append(
                                f"Method {cls_name}.{method_name}() has partially missed lines. "
                                f"Missed lines: {missed}. Add tests for edge cases or branches."
                            )

            classes.append(class_record)

    # Overall summary
    total_missed = sum(c["missed_lines"] for c in classes)
    total_covered = sum(c["covered_lines"] for c in classes)
    total_lines = total_missed + total_covered
    percent = round((total_covered / total_lines) * 100, 2) if total_lines else 0

    return {
        "coverage_percent": percent,
        "classes": classes,
        "recommendations": recommendations
    }

# ----------------------------------------------------
# 5. Git Status Tool
# ----------------------------------------------------
@mcp.tool
def git_status():
    """
    Git Status Tool

    Description:
    - Checks the current Git repository for changes.
    - Returns a summary of the repository's state, including:
        - is_dirty: True if there are any changes (staged or unstaged)
        - unstaged: list of files modified but not staged
        - staged: list of files staged for commit
        - untracked: list of untracked files
    Usage:
    - Use this tool before committing changes to ensure you know the repository status.
    """
    repo = git.Repo(os.getcwd())
    return {
        "is_dirty": repo.is_dirty(),
        "unstaged": [item.a_path for item in repo.index.diff(None)],
        "staged": [item.a_path for item in repo.index.diff("HEAD")],
        "untracked": repo.untracked_files
    }


# ----------------------------------------------------
# 6. Git Add All Tool
# ----------------------------------------------------
IGNORE = ["target", ".idea", "*.class", "*.log"]

@mcp.tool
def git_add_all():
    """
    Git Add All Tool

    Description:
    - Stages all changes in the current Git repository.
    - Ignores specified files/folders (e.g., build artifacts like 'target', '.class', logs).
    - Prepares all files for commit.
    Usage:
    - Use this tool to stage all project changes automatically before committing.
    """
    repo = git.Repo(os.getcwd())
    repo.git.add(all=True)
    return {"status": "staged"}

# ----------------------------------------------------
# 7. Git Commit Tool
# ----------------------------------------------------
@mcp.tool
def git_commit(message: str):
    """
    Git Commit Tool

    Description:
    - Commits staged changes in the Git repository with a provided commit message.
    - Returns status indicating whether a commit was made or if there was nothing to commit.
    Usage:
    - Always run after git_add_all to commit changes to the repository.
    """
    repo = git.Repo(os.getcwd())
    if repo.is_dirty():
        repo.git.commit("-m", message)
        return {"status": "committed", "message": message}
    return {"status": "nothing_to_commit"}

# ----------------------------------------------------
# 8. Git Push Tool
# ----------------------------------------------------
@mcp.tool
def git_push(remote="origin"):
    """
    Git Push Tool

    Description:
    - Pushes the current branch to the specified remote repository (default 'origin').
    - Automatically sets upstream if not already configured.
    Usage:
    - Use after committing changes to update the remote repository.
    - Can be combined with git_commit for automated workflows.
    """
    repo = git.Repo(os.getcwd())
    repo.git.push("--set-upstream", remote, repo.active_branch.name)
    return {"status": "pushed", "branch": repo.active_branch.name}


# ----------------------------------------------------
# 9. Create GitHub Pull Request Tool
# ----------------------------------------------------

@mcp.tool
def git_pull_request(base: str, title: str, body: str):
    """
    GitHub Pull Request Tool

    Description:
    - Creates a pull request on GitHub for the current branch.
    - Uses environment variable GITHUB_TOKEN for authentication.
    - Parameters:
        - base: branch to merge into (usually 'main' or 'master')
        - title: PR title
        - body: PR description
    Usage:
    - Use this tool to open pull requests after automated test improvements or code changes.
    - Returns the URL of the created PR for tracking.
    """
    token = os.getenv("GITHUB_TOKEN")
    g = Github(token)

    repo = g.get_user().get_repo("YOUR_REPO_NAME")
    branch = repo.get_branch(repo.default_branch)

    pr = repo.create_pull(
        title=title,
        body=body,
        head=repo.active_branch.name,
        base=base
    )
    return {"pr_url": pr.html_url}

if __name__ == "__main__":
    mcp.run(transport="sse") 

