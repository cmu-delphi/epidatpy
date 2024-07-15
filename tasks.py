"""
Tasks for maintaining the project.

Execute 'invoke --list' for guidance on using Invoke
"""

import shutil
import webbrowser
from pathlib import Path

from invoke import task

ROOT_DIR = Path(__file__).parent
TEST_DIR = ROOT_DIR.joinpath("tests")
SOURCE_DIR = ROOT_DIR.joinpath("epidatpy")
TOX_DIR = ROOT_DIR.joinpath(".tox")
COVERAGE_FILE = ROOT_DIR.joinpath(".coverage")
COVERAGE_DIR = ROOT_DIR.joinpath("htmlcov")
COVERAGE_REPORT = COVERAGE_DIR.joinpath("index.html")
DOCS_DIR = ROOT_DIR.joinpath("docs")
DOCS_BUILD_DIR = DOCS_DIR.joinpath("_build")
DOCS_INDEX = DOCS_BUILD_DIR.joinpath("index.html")
PYTHON_DIRS = [str(d) for d in [SOURCE_DIR, TEST_DIR]]
JOINED_PYTHON_DIRS = " ".join(PYTHON_DIRS)


def _delete_file(file: Path) -> None:
    try:
        file.unlink(missing_ok=True)
    except TypeError:
        # missing_ok argument added in 3.8
        try:
            file.unlink()
        except FileNotFoundError:
            pass


@task()
def format(c):  # pylint: redefined-builtin
    """
    Format code
    """
    c.run("black --config pyproject.toml {}".format(JOINED_PYTHON_DIRS))


@task
def lint_black(c):
    c.run("black --check --config pyproject.toml {}".format(JOINED_PYTHON_DIRS))


@task
def lint_pylint(c):
    c.run("pylint {}".format(JOINED_PYTHON_DIRS))


@task
def lint_mypy(c):
    c.run("mypy --ignore-missing-imports {}".format(JOINED_PYTHON_DIRS))


@task(pre=[lint_black, lint_pylint, lint_mypy])
def lint(c):  # pylint: disable=unused-argument
    """
    Lint code
    """


@task
def test(c):
    """
    Run tests
    """
    c.run("pytest {}".format(TEST_DIR))


@task(help={"publish": "Publish the result via coveralls"})
def coverage(c, publish=False):
    """
    Create coverage report
    """
    c.run("coverage run --source {} -m pytest".format(TEST_DIR))
    c.run("coverage report")
    if publish:
        # Publish the results via coveralls
        c.run("coveralls")
    else:
        # Build a local report
        c.run("coverage html")
        webbrowser.open(COVERAGE_REPORT.as_uri())


@task
def docs(c):  # type: ignore
    """
    Generate documentation
    """
    c.run("sphinx-build -b html {} {}".format(DOCS_DIR, DOCS_BUILD_DIR))
    webbrowser.open(DOCS_INDEX.as_uri())


@task
def clean_docs(c):  # pylint: disable=unused-argument
    """
    Clean up files from documentation builds
    """
    shutil.rmtree(DOCS_BUILD_DIR, ignore_errors=True)


@task
def clean_build(c):
    """
    Clean up files from package building
    """
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree(".eggs", ignore_errors=True)
    c.run("find . -name '*.egg-info' -exec rm -fr {} +")
    c.run("find . -name '*.egg' -exec rm -f {} +")


@task
def clean_python(c):
    """
    Clean up python file artifacts
    """
    c.run("find . -name '*.pyc' -exec rm -f {} +")
    c.run("find . -name '*.pyo' -exec rm -f {} +")
    c.run("find . -name '__pycache__' -exec rm -fr {} +")


@task
def clean_tests(c):  # pylint: disable=unused-argument
    """
    Clean up files from testing
    """
    _delete_file(COVERAGE_FILE)
    shutil.rmtree(TOX_DIR, ignore_errors=True)
    shutil.rmtree(COVERAGE_DIR, ignore_errors=True)


@task(pre=[clean_build, clean_python, clean_tests, clean_docs])
def clean(c):  # pylint: disable=unused-argument
    """
    Runs all clean sub-tasks
    """


@task(clean)
def dist(c):
    """
    Build source and wheel packages
    """
    c.run("python -m build --sdist --wheel")


@task(pre=[clean, dist])
def release(c):
    """
    Make a release of the python package to pypi
    """
    c.run("twine upload dist/*")
