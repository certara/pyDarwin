
*************
Installation
*************

System Requirements
--------------------

Windows
^^^^^^^^

- Windows 10
- Windows Server 2018/2019

Linux
^^^^^^^^

- CentOS8/RHEL8
- Ubuntu >= 18.0.4


Hardware Requirements
-----------------------


Minimum and recommended requirements:

+--------------------------+----------------------------+----------------------------+
|                          | Minimum                    | Recommended                |
+==========================+============================+============================+
| Processor                | Intel i5 processor 3 GHz   | Intel i7 processor 4 GHz   |
+--------------------------+----------------------------+----------------------------+
| Number of physical cores | 4                          | 16                         |
+--------------------------+----------------------------+----------------------------+
| RAM                      | 16 GB RAM                  | 32 GB RAM                  |
+--------------------------+----------------------------+----------------------------+
| Internal Storage Device  | 1 GB HDD                   | 100 GB SSD                 |
+--------------------------+----------------------------+----------------------------+


Grid Computing Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

pyDarwin may be executed on Linux hosts with Sun Grid Engine (SGE).
 
Software Requirements
-----------------------

- Python >= 3.10
- NONMEM >= 7.4.3
- R >= 4.0.0 (optional)

Install pyDarwin
-----------------------

.. _install_python_venv:

Before installing ``pyDarwin``, we recommend creating a python virtual environment to maintain isolation of package dependencies. From the 
command line, type:

.. code:: python

   python -m venv .venv

.. code:: bash

   .venv/Scripts/activate

Both the development version and released version of ``pyDarwin`` are available to install via ``pip`` from Certara's managed PyPi repository. 

.. tabs::

      .. group-tab:: Released

         .. code-block:: python

             pip install pyDarwin-Certara --index-url https://certara.jfrog.io/artifactory/api/pypi/certara-pypi-release-public/simple --extra-index-url https://pypi.python.org/simple/

      .. group-tab:: Development

         .. code-block:: python

            pip install pyDarwin-Certara --index-url https://certara.jfrog.io/artifactory/api/pypi/certara-pypi-develop-local/simple --extra-index-url https://pypi.python.org/simple/
