.. pyDarwin documentation master file, created by
   sphinx-quickstart on Thu Jun  9 08:53:00 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

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

+-------------------------+----------------------------+----------------------------+
|                         | Minimum                    | Recommended                |
+=========================+============================+============================+
| Processor               | Intel i5 processor 3 GHz   | Intel i7 processor 4 GHz   |
+-------------------------+----------------------------+----------------------------+
| RAM                     | 16 GB RAM                  | 32 GB RAM                  |
+-------------------------+----------------------------+----------------------------+
| Internal Storage Device | 1 GB 7200 RPM Magnetic HD  | 1 GB SSD                   |
+-------------------------+----------------------------+----------------------------+


Grid Computing Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

pyDarwin may be executed on Linux hosts with Sun Grid Engine (SGE).
 
Software Requirements
-----------------------

- Python >= 3.10
- NONMEM >= 7.4.3
- R >= 4.0.0 (optional)

*Note: Requirements are Python and NONMEM installation with nmfe.bat available. R installation is required if using* ``"postRunRcode"`` *in* ``options.json`` *with* ``"useR" : true``.

Install pyDarwin
-----------------------

Before installing ``pyDarwin`` we recommend creating a python virtual environment to in order maintain isolation of package dependencies. 

.. code:: python

   python -m venv .venv

.. code:: bash

   .venv/Scripts/activate

Both the development version and released version of pyDarwin are available to install via ``pip`` from Certara's managed PyPi repository. 

Development 
^^^^^^^^^^^^^^

.. code:: python

   pip install pyDarwin-Certara --index-url https://certara.jfrog.io/artifactory/api/pypi/certara-pypi-develop-local/simple --extra-index-url https://pypi.python.org/simple/

Released 
^^^^^^^^^^^^^^

.. code:: python

   pip install pyDarwin-Certara --index-url https://certara.jfrog.io/artifactory/api/pypi/certara-pypi-develop-local/simple --extra-index-url https://pypi.python.org/simple/
