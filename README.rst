|coverage| |maintainability| |precommit_ci| |docs| |style| |version| |status| |pyversions|


.. |docs| image:: https://readthedocs.org/projects/my-app/badge/
    :alt: Documentation Status
    :target: https://my-app.readthedocs.io/en/latest/?badge=latest

.. |coverage| image:: https://codecov.io/gh/MiraGeoscience/my-app/branch/develop/graph/badge.svg
    :alt: Code coverage
    :target: https://codecov.io/gh/MiraGeoscience/my-app

.. |style| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :alt: Coding style
    :target: https://github.com/pf/black

.. |version| image:: https://img.shields.io/pypi/v/my-app.svg
    :alt: version on PyPI
    :target: https://pypi.python.org/pypi/my-app/

.. |status| image:: https://img.shields.io/pypi/status/my-app.svg
    :alt: version status on PyPI
    :target: https://pypi.python.org/pypi/my-app/

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/my-app.svg
    :alt: Python versions
    :target: https://pypi.python.org/pypi/my-app/

.. |precommit_ci| image:: https://results.pre-commit.ci/badge/github/MiraGeoscience/my-app/develop.svg
    :alt: pre-commit.ci status
    :target: https://results.pre-commit.ci/latest/github/MiraGeoscience/my-app/develop

.. |maintainability| image:: https://api.codeclimate.com/v1/badges/_token_/maintainability
   :target: https://codeclimate.com/github/MiraGeoscience/my-app/maintainability
   :alt: Maintainability


my-app: # TODO: SHORT DESCRIPTION
=========================================================================
The **my-app** library # TODO: PACKAGE DESCRIPTION

.. contents:: Table of Contents
   :local:
   :depth: 3

Documentation
^^^^^^^^^^^^^
`Online documentation <https://my-app.readthedocs.io/en/latest/>`_


Installation
^^^^^^^^^^^^
**my-app** is currently written for Python 3.10 or higher.

Install Conda
-------------

To install **my-app**, you need to install **Conda** first.

We recommend to install **Conda** using `miniforge`_.

.. _miniforge: https://github.com/conda-forge/miniforge

Within a conda environment
--------------------------

You can install (or update) a conda environment with all the requires packages to run **my-app**.
To do so you can directly run the **Install_or_Update.bat** file by double left clicking on it.

Install with conda
------------------

You can install the package using ``conda`` and the ``.lock`` files from a conda prompt:

.. code-block:: bash

  conda env create -n my-env -f environments/[the_desired_env].lock.yml

Install with PyPI
-----------------

You should not install the package from PyPI, as the app requires conda packages to run.
Still, you can install it in a conda environment without its dependencies (``--no-deps``).

From PyPI
~~~~~~~~~

To install the **my-app** package published on PyPI:

.. code-block:: bash

    pip install -U --no-deps my-app

From a Git tag or branch
~~~~~~~~~~~~~~~~~~~~~~~~
If the package is not on PiPY yet, you can install it from a Git tag:

.. code-block:: bash

    pip install -U --no-deps --force-reinstall https://github.com/MiraGeoscience/my-app/archive/refs/tags/TAG.zip

Or to install the latest changes available on a given Git branch:

.. code-block:: bash

    pip install -U --no-deps --force-reinstall https://github.com/MiraGeoscience/my-app/archive/refs/heads/BRANCH.zip

.. note::
    The ``--force-reinstall`` option is used to make sure the updated version
    of the sources is installed, and not the cached version, even if the version number
    did not change. The ``-U`` or ``--upgrade`` option is used to make sure to get the latest version,
    on not merely reinstall the same version. As the package is aimed to be in a **Conda environment**, the option ``--no-deps`` is used to avoid installing the dependencies with pip, as they will be installed with conda.

From a local copy of the sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you have a git clone of the package sources locally,
you can install **my-app** from the local copy of the sources with:

.. code-block:: bash

    pip install -U --force-reinstall path/to/project_folder_with_pyproject_toml

Or in **editable mode**, so that you can edit the sources and see the effect immediately at runtime:

.. code-block:: bash

    pip install -e -U --force-reinstall path/to/project_folder_with_pyproject_toml

Setup for development
^^^^^^^^^^^^^^^^^^^^^

Create the .lock files
----------------------

First, you need to create the ``.lock`` files for the dependencies defined in ``pyproject.toml``.
To do so, double click on ``devtools\run-conda-lock.bat`` or execute it from command line:

.. code-block:: bash

    $ [path/to/my-app]/devtools/run_conda_lock.bat

It will create ``.lock`` in the ``environments`` folder.
The created ``.lock`` files are the combination of python version and platforms.
The platforms are specified in ``conda-lock`` section of the ``pyproject.toml`` file:

.. code-block::

    [tool.conda-lock]
    platforms = ['win-64', 'linux-64']

The python versions are specified at the beginning of the ``devtools\run-conda-lock.py`` file:

.. code-block::

    _python_versions = ["3.10", "3.9"]

The ``Install_or_Update.bat`` and the ``setup-dev.bat`` will use them to install the environment.

Anytime dependencies are added or removed to the ``pyproject.toml`` file, you need to run ``run-conda-lock.bat`` again. Run it as well when you want to fetch newly available versions of the dependencies (typically patches, still in accordance with the specifications expressed in ``pyproject.toml``).

Install the conda environment
-----------------------------

For development, you need a **conda** environments. you can install it running the ``setup-dev.bat`` or:

.. code-block:: bash

    $ [path/to/my-app]/devtools/setup-dev.bat

This command install a local environment at the base of your repository: ``.conda-env``.
This environment should automatically be recognized by the conda installation.

Configure the pre-commit hooks
------------------------------

`pre-commit`_ is used to automatically run static code analysis upon commit.
The list of tools to execute upon commit is configured in the file `.pre-commit-config.yaml`_.

pre-commit can be installed using a Python installation on the system, or one from a conda environment.

- To install pre-commit using Python (and pip) in your system path:

..  code-block:: bash

    pip install --user pre-commit

- Or to install from an activated conda environment:

..  code-block:: bash

    conda install -c conda-forge pre-commit

Then, in either way, install the pre-commit hooks as follow (**current directory is the project folder**):

..  code-block:: bash

    pre-commit install

To prepare and check the commit messages, you can also use the following commands:

.. code-block:: bash

    pre-commit install -t prepare-commit-msg -t commit-msg

It configures ``pre-commit`` to prepares and checks the commit ensuring it has a JIRA issue ID: if no ID was provided, it extracts it from the branch name. If one was provided, it checks it is the same one as in the branch name.

To run pre-commit manually, use the following command:

..  code-block:: bash

    pre-commit run --all-files

To run only on changes staged for commit:

.. code-block:: bash

    pre-commit run

If a tool fails running, it might be caused by an obsolete versions of the tools that pre-commit is trying to execute.
Try the following command to update them:

..  code-block:: bash

    pre-commit autoupdate

Upon every commit, all the pre-commit checks run automatically for you, and reformat files when required. Enjoy...

If you prefer to run pre-commit upon push, and not upon every commit, use the following commands:

..  code-block:: bash

    pre-commit uninstall -t pre-commit
    pre-commit install -t pre-push

.. _pre-commit: https://pre-commit.com/

Running the tests
-----------------
Test files are placed under the ``tests`` folder. Inside this folder and sub-folders,
Python test files are to be named with ``_test.py`` as a suffix.
The test function within this files must have a ``test_`` prefix.

Install pytest
~~~~~~~~~~~~~~

.. _pytest: https://docs.pytest.org/

If you installed  your environment through ``setup-dev.bat``, pytest is already installed.
You can run it from the conda command (**in your project folder**):

.. code-block:: bash

    (my-dev-env) pytest tests

Code coverage with Pytest
-------------------------
.. _pytest-cov: https://pypi.org/project/pytest-cov/

If you installed  your environment through ``setup-dev.bat``, `pytest-cov`_ is already installed.
It allows you to visualize the code coverage of your tests.
You can run the tests from the console with coverage:

.. code-block:: bash

    (my-env) pytest --cov=my_app --cov-report html tests

The html report is generated in the folder ``htmlcov`` at the root of the project.
You can then explore the report by opening ``index.html`` in a browser.

Git LFS
-------
In the case your package requires large files, `git-lfs`_ can be used to store those files.
Copy it from the `git-lfs`_ website, and install it.

Then, in the project folder, run the following command to install git-lfs:

.. code-block:: bash

    git lfs install


It will update the file ``.gitattributes`` with the list of files to track.

Then, add the files and the ``.gitattributes`` to the git repository, and commit.

.. _git-lfs: https://git-lfs.com/

Then, add the files to track with git-lfs:

.. code-block:: bash

    git lfs track "*.desire_extension"

IDE : PyCharm
-------------
`PyCharm`_, by JetBrains, is a very good IDE for developing with Python.

Configure the Python interpreter in PyCharm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, excluded the ``.conda-env`` folder from PyCharm.
Do so, in PyCharm, right-click on the ``.conda-env`` folder, and ``Mark Directory as > Excluded``.

Then, you can add the conda environment as a Python interpreter in PyCharm.

    ..  image:: devtools/images/pycharm-exclude_conda_env.png
        :alt: PyCharm: Exclude conda environment
        :align: center
        :width: 40%


In PyCharm settings, open ``File > Settings``, go to ``Python Interpreter``,
and add click add interpreter (at the top left):

    ..  image:: devtools/images/pycharm-add_Python_interpreter.png
        :alt: PyCharm: Python interpreter settings
        :align: center
        :width: 80%

Select ``Conda Environment``, ``Use existing environment``,
and select the desired environment from the list (the one in the ``.conda-env`` folder):

    ..  image:: devtools/images/pycharm-set_conda_env_as_interpreter.png
        :alt: PyCharm: Set conda environment as interpreter
        :align: center
        :width: 80%

Then you can check the list of installed packages in the ``Packages`` table. You should see
**my-app** and its dependencies. Make sure to turn off the ``Use Conda Package Manager``
option to see also the packages installed through pip:

    ..  image:: devtools/images/pycharm-list_all_conda_packages.png
        :alt: PyCharm: Conda environment packages
        :align: center
        :width: 80%


Run the tests from PyCharm
~~~~~~~~~~~~~~~~~~~~~~~~~~
First, right click on the ``tests`` folder and select ``Mark Directory as > Test Sources Root``:

    ..  image:: devtools/images/pycharm-mark_directory_as_tests.png
        :alt: PyCharm: Add Python interpreter
        :align: center
        :width: 40%

You can now start tests with a right click on the ``tests`` folder and
select ``Run 'pytest in tests'``, or select the folder and just hit ``Ctrl+Shift+F10``.

PyCharm will nicely present the test results and logs:

    ..  image:: devtools/images/pycharm-test_results.png
        :alt: PyCharm: Run tests
        :align: center
        :width: 80%

Execute tests with coverage from PyCharm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can run the tests with a nice report of the code coverage, thanks to the pytest-cov plugin
(already installed in the virtual environment as development dependency as per `pyproject.toml`_).


To set up this option in PyCharm, right click on the ``tests`` folder and ``Modify Run Configuration...``,
then add the following option in the ``Additional Arguments`` field:

    ..  image:: devtools/images/pycharm-menu_modify_test_run_config.png
        :alt: PyCharm tests contextual menu: modify run configuration
        :width: 30%

    ..  image:: devtools/images/pycharm-dialog_edit_test_run_config.png
        :alt: PyCharm dialog: edit tests run configuration
        :width: 60%

select ``pytest in tests``, and add the following option in the ``Additional Arguments`` field::

..code-block:: bash

    --cov=my_app --cov-report html

Then, run the tests as usual, and you will get a nice report of the code coverage.

Some useful plugins for PyCharm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Here is a suggestion for some plugins you can install in PyCharm.

- `Toml`_, to edit and validate ``pyproject.toml`` file.
- `IdeaVim`_, for Vim lovers.
- `GitHub Copilot`_, for AI assisted coding.

.. _PyCharm: https://www.jetbrains.com/pycharm/

.. _Toml: https://plugins.jetbrains.com/plugin/8195-toml/
.. _IdeaVim: https://plugins.jetbrains.com/plugin/164-ideavim/
.. _GitHub Copilot: https://plugins.jetbrains.com/plugin/17718-github-copilot

.. _pyproject.toml: pyproject.toml
.. _.pre-commit-config.yaml: .pre-commit-config.yaml

License
^^^^^^^
# TODO: ADD LICENSE TERMS

Third Party Software
^^^^^^^^^^^^^^^^^^^^
The my-app Software may provide links to third party libraries or code (collectively “Third Party Software”)
to implement various functions. Third Party Software does not comprise part of the Software.
The use of Third Party Software is governed by the terms of such software license(s).
Third Party Software notices and/or additional terms and conditions are located in the
`THIRD_PARTY_SOFTWARE.rst`_ file.

.. _THIRD_PARTY_SOFTWARE.rst: THIRD_PARTY_SOFTWARE.rst

Copyright
^^^^^^^^^
Copyright (c) 2023 Mira Geoscience Ltd.
