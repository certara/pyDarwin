.. _startExamples:

################################################################
Examples
################################################################

The following examples are provided in |ReleaseVersion| to help you get started.
`Examples <https://github.com/certara/pyDarwin/tree/master/examples/user>`_ are
organized into folders with all required files available for execution.

.. toctree::
   :hidden:

   Example1
   Example2
   Example3
   Example4
   Example5
   Example6
   Example7
   Example8
   Example9
   Example10

* :ref:`Example 1: PK Model, Trivial Exhaustive Search <startpk1>`

* :ref:`Example 2: PK Model 2, Simulation model by GP with Python code <startpk2>`

* :ref:`Example 3: PK Model, ODE model <startpk3>`

* :ref:`Example 4: PK Model, DMAG by GA with post-run R code <startpk4>`

* :ref:`Example 5: PK Model, DMAG by GP <startpk5>`

* :ref:`Example 6: PK Model, DMAG by RF with post-run Python code <startpk6>`

* :ref:`Example 7: PK Model, Exhaustive Omega Search <startpk7>`

* :ref:`Example 8: Emax Model, PSO <startpd8>`
 
* :ref:`Example 9: MOGA <startmoga9>`

* :ref:`Example 10: MOGA3 <startmoga10>`

.. _examples_target:

To get started, download and unzip the `Examples <https://github.com/certara/pyDarwin/tree/master/examples/user>`_
folders from the following `link <https://certara-training.s3.amazonaws.com/Certara+Darwin+Project/pyDarwin_1_1_Examples.zip>`_.

After setting up your :ref:`Python virtual environment <install_python_venv>` and :ref:`installing pyDarwin <install_pyDarwin>`,
you can simply specify the path to the one of the Example[n] folders in the command below and the search will begin:

.. code-block:: ps1

    python -m darwin.run_search_in_folder ./Example1

.. note::

    You may need to edit the path to NONMEM executable e.g., :ref:`nmfe_path <nmfe_path_options_desc>` in the
    :ref:`options.json <Options>` file inside each of the example folders to point to the correct location on your machine.
