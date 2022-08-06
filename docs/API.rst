API
==============

High level functions
~~~~~~~~~~~~~~~~~~~~~~~

run\_search
-------------------------
.. _darwin.run_search:

.. automodule:: darwin.run_search
   :members:

run\_search\_in\_folder
--------------------------
.. _darwin.run_search_in_folder:

.. automodule:: darwin.run_search_in_folder
   :members:
   :undoc-members:

Algorithms
~~~~~~~~~~~~~~~~~~~~~~~

exhaustive
-----------------------------------

.. automodule:: darwin.algorithms.exhaustive
   :members:
   :undoc-members:

GA
---------------------------

.. automodule:: darwin.algorithms.GA
   :members:
   :undoc-members:

OPT
----------------------------

.. automodule:: darwin.algorithms.OPT
   :members:
   :undoc-members:

PSO
----------------------------

.. automodule:: darwin.algorithms.PSO
   :members: run_pso
   :undoc-members:

downhill
--------------------------------------

.. automodule:: darwin.algorithms.run_downhill
   :members:
   :undoc-members:

Model classes
~~~~~~~~~~~~~~~~~~~~~~~

darwin.Template
----------------------

.. automodule:: darwin.Template
   :members:
   :undoc-members:

darwin.Model
-------------------

.. automodule:: darwin.Model
   :members:
   :undoc-members:

darwin.ModelCode
-----------------------

.. automodule:: darwin.ModelCode
   :members:
   :undoc-members:
   :private-members:
   :exclude-members: _int_to_bin, _code_to_str, _restore_code

darwin.ModelResults
--------------------------

.. automodule:: darwin.ModelResults
   :members:
   :undoc-members:

darwin.ModelRun
----------------------

.. automodule:: darwin.ModelRun
   :members:
   :undoc-members:
   :exclude-members: model_result_class

darwin.Population
------------------------

.. automodule:: darwin.Population
   :members:
   :undoc-members:
   :special-members: __init__

.. _api_model_cache:

Caching model runs
~~~~~~~~~~~~~~~~~~~~~~~
| It's not uncommon to get duplicated models during search. In order to prevent unnecessary runs all unique models from current search are stored in Model Cache.
| Every new model is checked against the cache. If a match is found, the new model is replaced with cached one, so the result is obtained instantly.
| Currently only in-memory cache is available, so in case of large searches (millions of model runs) memory footprint may be substantial.
| Normally the cache is dumped at the end of every iteration or when you :ref:`stop the search <stop_search>`. This behaviour can be affected 
   by :ref:`saved_models_readonly <saved_models_readonly_options_desc>` set to true. You also can load the cache from :ref:`saved state <use_saved_models_options_desc>`.

darwin.ModelCache
------------------------

.. automodule:: darwin.ModelCache
   :members:
   :undoc-members:

darwin.MemoryModelCache
------------------------------

.. automodule:: darwin.MemoryModelCache
   :members:
   :undoc-members:
   :show-inheritance:
   :no-private-members:

Model run strategies
~~~~~~~~~~~~~~~~~~~~~~~

darwin.ModelRunManager
-----------------------------

.. automodule:: darwin.ModelRunManager
   :members:
   :undoc-members:

darwin.PipelineRunManager
--------------------------------

.. automodule:: darwin.PipelineRunManager
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members:
   :exclude-members: _abc_impl, _copy_to_best

darwin.LocalRunManager
-----------------------------

.. automodule:: darwin.LocalRunManager
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members: _create_model_pipeline

Execution on grid
~~~~~~~~~~~~~~~~~~~~~~~

darwin.grid.GridRunManager
---------------------------------

.. automodule:: darwin.grid.GridRunManager
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members:
   :exclude-members: _abc_impl

darwin.grid.GridAdapter
------------------------------

.. automodule:: darwin.grid.GridAdapter
   :members:
   :undoc-members:

darwin.grid.GenericGridAdapter
-------------------------------------

.. automodule:: darwin.grid.GenericGridAdapter
   :members:
   :undoc-members:
   :show-inheritance:

Modelling engines
~~~~~~~~~~~~~~~~~~~~~~~

darwin.ModelEngineAdapter
---------------------------------

.. automodule:: darwin.ModelEngineAdapter
   :members:
   :undoc-members:

darwin.nonmem.NMEngineAdapter
------------------------------------

.. automodule:: darwin.nonmem.NMEngineAdapter
   :members:
   :show-inheritance:
   :undoc-members:

darwin.nonmem.utils module
--------------------------

.. automodule:: darwin.nonmem.utils
   :members:
   :undoc-members:
   :private-members:

Utilities
~~~~~~~~~~~~~~~~~~~~~~~

darwin.utils module
-------------------

.. automodule:: darwin.utils
   :members:
   :show-inheritance:
   :undoc-members:

darwin.DarwinApp module
-----------------------

.. automodule:: darwin.DarwinApp
   :members:
   :undoc-members:

darwin.ExecutionManager module
------------------------------

.. automodule:: darwin.ExecutionManager
   :members:
   :undoc-members:

darwin.Log module
-----------------

.. automodule:: darwin.Log
   :members:
   :undoc-members:

darwin.options module
---------------------

.. automodule:: darwin.options
   :members:
   :undoc-members:

Runnable modules
~~~~~~~~~~~~~~~~~~~~~~~

darwin.run\_search
-------------------------------------

darwin.run\_search\_in\_folder
-------------------------------------

darwin.stop\_search
--------------------------

darwin.run\_model
--------------------------

darwin.grid.run\_search
-------------------------------------

darwin.grid.run\_search\_in\_folder
-------------------------------------
