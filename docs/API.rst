.. include:: .special.rst

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
| Duplicate models are commonly encountered during search. To prevent unnecessary runs, all unique models from current search are stored in Model Cache.
| Every new model is checked against the cache. If a match is found, the new model is replaced with cached one, so the result is obtained instantly.
| Currently, only in-memory cache is available, so with large searches (millions of model runs), the memory footprint may be substantial.
| Normally the cache is dumped at the end of every iteration or when you :ref:`stop the search <stop_search>`. This behaviour can be affected 
   by :ref:`saved_models_readonly <saved_models_readonly_options_desc>` being set to true. You also can load the cache from a :ref:`saved state <use_saved_models_options_desc>`.

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
