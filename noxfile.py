"""Nox configuration file for NEMO."""

import nox

srcdirs = ['nemo', 'tests']
scripts = ['evolve', 'replay', 'summary']
RUFFIGNORE_BASE = "ANN,D203,D213,Q000"
RUFFIGNORE_PY = RUFFIGNORE_BASE + ',I001,ARG002,PLR,N801,INP,PT'
RUFFIGNORE_SCRIPTS = RUFFIGNORE_BASE + ',T201'


@nox.session
def codespell(session):
    """Run codespell."""
    ignorewords = "assertin, fom, hsa, trough, harge"
    session.install('codespell')
    session.run('codespell', '-d', '-L', f'{ignorewords}', *srcdirs)


@nox.session(python=["3.12", "3.13"])  # broken in 3.14
def bandit(session):
    """Run bandit."""
    session.install('bandit')
    session.run('bandit', '-r', '-qq', 'B101', *srcdirs)


@nox.session(python=["3.12", "3.13", "3.14"])
def isort(session):
    """Run isort."""
    session.install('isort')
    session.run('isort', '--check', *srcdirs)


@nox.session(python=["3.12", "3.13", "3.14"])
def vulture(session):
    """Run vulture."""
    session.install('vulture')
    session.run('vulture', '--min-confidence=70', *srcdirs)


@nox.session(python=["3.12", "3.13", "3.14"])
def pydocstyle(session):
    """Run pydocstyle."""
    session.install('pydocstyle')
    session.run('pydocstyle', *srcdirs)


@nox.session(python=["3.12", "3.13", "3.14"])
def pylama(session):
    """Run pylama."""
    session.install('pylama', 'setuptools')
    session.run('pylama', *srcdirs)


@nox.session(python=["3.12", "3.13", "3.14"])
def flake8(session):
    """Run flake8."""
    session.install('flake8')
    session.run('flake8', '--ignore=N801', *srcdirs)


@nox.session(python=["3.12", "3.13", "3.14"])
def pylint(session):
    """Run pylint."""
    session.install('pylint', 'matplotlib', 'requests', 'pytest', 'pint')
    session.run('pylint', '--enable=useless-suppression', '--ignore',
                '.nox', '--recursive', 'y', *srcdirs)


@nox.session(python=["3.12", "3.13", "3.14"])
def pytest(session):
    """Run pytest."""
    session.install('pytest', 'pytest-mpl', 'pytest-cov', 'pandas', 'numpy',
                    'requests', 'matplotlib', 'pint', 'pytest')
    session.run('pytest', '--mpl', '--cov=nemo', '--doctest-modules', *srcdirs)


@nox.session(python=["3.12", "3.13", "3.14"])
def ruff(session):
    """Run ruff."""
    session.install('ruff')
    session.run('ruff', 'check', '--select=ALL', f'--ignore={RUFFIGNORE_PY}',
                '--exclude=doc', '--output-format=concise', *srcdirs)
    session.run('ruff', 'check', '--select=ALL',
                f'--ignore={RUFFIGNORE_SCRIPTS}',
                '--exclude=doc', '--output-format=concise', *scripts)
