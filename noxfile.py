import nox

nox.options.sessions = ["lint", "test"]
nox.options.reuse_existing_virtualenvs = True

PYTHON_VERSIONS = ["3.10", "3.11"]

SRC = "places"


@nox.session(python=PYTHON_VERSIONS[0])
def lint(session: nox.Session) -> None:
    session.install("-e", ".")
    # Don't install all dev deps, only what's needed for linting
    session.install("ruff")
    session.run("ruff", SRC)


@nox.session(python=PYTHON_VERSIONS)
def test(session: nox.Session) -> None:
    session.install("-e", ".")
    # Don't install all dev deps, only what's needed for the tests
    session.install("pytest")
    session.run("pytest", SRC)

    session.run("places", "--help", silent=True)
