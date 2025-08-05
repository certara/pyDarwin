.. include:: .special.rst

NLME integration
===============================================

Basic Model Structure and Statements
------------------------------------------------------------------------

A PML model defines the structure of a
pharmacokinetic/pharmacodynamic model. The basic structure consists of a
main block enclosed in curly braces, typically named ``test()``,
containing statements that define the model's components.

The fundamental structure of a PML model is:

.. code:: pml

   modelName() {
     // Statements defining the model
   }

-  ``modelName()``: The name of the model (e.g., ``test``,
   ``oneCompartmentModel``). The parentheses ``()`` are *required*.
   While any valid name can be used, ``test()`` is a common convention
   for simple models.
-  ``{ ... }``: Curly braces define the *model block*. All model
   statements must be within this block.
-  Statements within the block define the model's components (e.g.,
   parameters, equations, error models). Statement order is generally
   *not* important, except within ``sequence`` blocks and for assignment
   statements.

**Keywords:** model, structure, test, block, curly braces, main block

**See also:** Statements, Blocks, Comments, Variables

Statements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Statements are the building blocks of a PML model. They
define parameters, equations, and other aspects of the model. Statements
can span multiple lines, and semicolons are optional separators.

-  **Types of Statements:** PML includes various statement types,
   including:

   -  Assignment statements (e.g., ``C = A1 / V``)
   -  Declaration statements (e.g., ``stparm``, ``fixef``, ``ranef``,
      ``covariate``, ``error``)
   -  Control flow statements (within ``sequence`` blocks: ``if``,
      ``while``, ``sleep``)
   -  Model component statements (e.g., ``deriv``, ``observe``,
      ``multi``, ``LL``, ``dosepoint``, ``cfMicro``)

-  **Order:** In general, the order of statements *does not matter* in
   PML, *except*:

   -  Within ``sequence`` blocks, where statements are executed
      sequentially.
   -  For assignment statements, where the order of assignments to the
      *same* variable matters.
   -  When defining micro constants before ``cfMicro``

-  **Semicolons:** Semicolons (``;``) are optional separators between
   statements. They can improve readability but are not required.
-  **Line Boundaries:** Statements can span multiple lines.

**Keywords:** statement, assignment, declaration, semicolon, order

**See also:** Basic PML Model Structure, Blocks, Variables, Assignment Statements

Blocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Blocks in PML are sets of statements enclosed in curly
braces ``{}``. They are used to group related statements and, in the
case of ``sequence`` blocks, to define a specific execution order.

-  **Main Model Block:** The entire model is enclosed in a block (e.g.,
   ``test() { ... }``).
-  **sequence Block:** The ``sequence`` block is a special type of
   block that defines a *sequence* of statements to be executed in
   order, at specific points in time. This is used for handling
   discontinuous events and time-dependent actions.
-  **Other Blocks:** There are no other named blocks besides the main
   model block and ``sequence`` blocks.
-  **dobefore, doafter blocks:** used to define some actions related to
   dose delivery and observations.

**Example (sequence block):**

.. code:: pml

   sequence {
     A = 10  // Initialize compartment A
     sleep(5) // Wait for 5 time units
     A = A + 5 // Add to compartment A
   }

**Keywords:** block, curly braces, sequence, scope

**See also:** Basic PML Model Structure, Statements, sequence block

Comments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comments are used to document the PML code, explaining its
purpose and functionality. PML supports three comment styles: R-style,
C-style, and C++-style.

-  **R-style:** ``# comment ... end-of-line`` (Everything after ``#`` on
   a line is a comment).
-  **C-style:** ``/* comment ... */`` (Multi-line comments, *cannot* be
   nested).
-  **C++-style:** ``// comment ... end-of-line``

**Example:**

.. code:: pml

   test() {
     # This is an R-style comment
     /* This is a
        multi-line C-style comment */
     deriv(A = -k * A)  // C++-style comment
     fixef(k = c(,3,))
     x = 5 //valid statement
     y = 1 #valid statement
   }

Important Note: While semicolons (;) are used as optional statement
separators in PML, they are NOT reliable comment markers. Do not use a
single semicolon to start a comment. The following examples demonstrate
correct and incorrect comment usage:

test() { deriv(A1 = k) stparm(k = tvk) # This works because 'stparm' is
valid. ; This is NOT a valid comment and will cause an error # This is a
valid R-style comment. // This is a valid C++-style comment. /\* This is
valid C-style multi-line comment. \*/ fixef(tvk = c(0,1,2)) }

**Keywords:** comment, documentation, #, /\* \*/, //

**See also:** Basic PML Model Structure

Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Variables in PML represent quantities within the model,
such as parameters, compartment amounts, and concentrations. Variables
can be declared explicitly or defined through assignment.

-  **Data Types:** All variables in PML are double-precision
   floating-point numbers (you can declare them using ``real`` or
   ``double``, which are equivalent).
-  **Declared Variables:** Introduced by declaration statements like
   ``deriv``, ``real``, ``stparm``, ``sequence``, and ``covariate``.
   These can be modified at specific points in time (e.g., within
   ``sequence`` blocks). Examples:

   -  ``deriv(A = -k * A)`` (Declares ``A`` as an integrator variable)
   -  ``real(x)`` (Declares ``x`` as a real variable, modifiable in
      ``sequence`` blocks)
   -  ``stparm(V = tvV * exp(nV))`` (Declares ``V`` as a structural
      parameter)

-  **Functional Variables:** Introduced by assignment at the *top level*
   of the model (i.e., not within a ``sequence`` block). These are
   considered to be continuously calculated and cannot be modified
   within ``sequence`` blocks. Example:

   -  ``C = A / V`` (Defines ``C`` as the concentration, calculated from
      ``A`` and ``V``)

-  **Variable Names:** Variable names must:

   -  Be case-sensitive
   -  Not contain special characters like "."
   -  Not begin with an underscore "\_"

-  **Predefined variables** PML contains predefined variables like ``t``

**Keywords:** variable, declaration, assignment, scope, real, double, declared, functional

**See also:** Statements, Assignment Statements, Declaration Statements, stparm, fixef, ranef, deriv, real

Predefined Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``t``. Represents time. This variable is automatically available in *time-based models* (models containing at least one ``deriv``    statement).

.. warning::
   The use of ``t`` on the right-hand-side of ``deriv`` statement is not recommended.

.. note::
   Contrary to some other modeling languages, ``pi`` (the mathematical constant ≈ 3.14159) is not a predefined
   variable in PML. You *must* define it explicitly (e.g., ``pi = 3.141592653589793``).

**Keywords:** predefined variables, t, time, built-in variables

**See also:** Variables, Time-Based Models, ``deriv`` Statement

Assignment Statements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assignment statements are used to define the value of a
variable based on an expression. They use the ``=`` operator. Variables
defined by top-level assignment are considered continuously calculated.

-  **Syntax:** ``variable = expression``
-  ``expression`` Can be any valid mathematical expression
   involving numbers, variables, operators, and functions.
-  **Top-Level Assignment:** Assignments made at the top level of the
   model (outside of ``sequence`` blocks) define *functional* variables.
   These are continuously updated as the values of the variables they
   depend on change.

.. note::
   Functional variables are analogous to variables defined by simple assignment within NONMEM's ``$PK`` or ``$PRED`` blocks (before the ``Y=`` line).

-  **Order matters:** The order of the statements matter.
-  **Multiple assignments:** It is allowable to have multiple assignment
   statements assigned to the same variable, in which case the order
   between them matters.
-  **Important Note:** Variables defined and assigned via top-level
   assignment *cannot* be modified within ``sequence`` blocks.

**Example:**

.. code:: pml

   test() {
     A = 10        # Assigns the value 10 to A
     V = 5         # Assigns the value 5 to V
     C = A / V     # Calculates C (concentration) continuously
     C = C + 2     # C will be equal to A/V + 2
   }

**Keywords:** assignment, =, equation, expression, continuous

**See also:** Variables, Statements

Parameter Declarations (stparm, fixef, ranef)
------------------------------------------------------------------------

stparm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``stparm`` statement defines structural parameters in
the model, which are the core parameters describing the
pharmacokinetic/pharmacodynamic processes. ``stparm`` statements can
include fixed effects, random effects, and covariate effects.

-  **Purpose:** Defines structural parameters and their relationships to
   fixed effects, random effects, and covariates.
-  **Syntax:** ``stparm(parameter = expression)``

   -  ``parameter``: The name of the structural parameter (e.g., ``V``,
      ``Cl``, ``Ka``, ``EC50``).
   -  ``expression``: An expression defining how the parameter is
      calculated. This expression can include:

      -  Fixed effects (typically named with a ``tv`` prefix, e.g.,
         ``tvV``).
      -  Random effects (typically named with an ``n`` prefix, e.g.,
         ``nV``).
      -  Covariates.
      -  Mathematical operators and functions.
      -  Time-dependent logic using the ternary operator (``? :``).

-  **Common Distributions:**

   -  **Log-Normal:** ``parameter = tvParameter * exp(nParameter)``
      (Parameter is always positive)
   -  **Normal:** ``parameter = tvParameter + nParameter``
   -  **Logit-Normal:** ``parameter = ilogit(tvParameter + nParameter)``
      (Parameter is between 0 and 1)

-  **Multiple stparm Statements:** A model can have multiple
   ``stparm`` statements.

.. note::   
   ``stparm`` defines *structural parameters*. These are typically the parameters you are interested in estimating.
   Variables defined by simple assignment in NONMEM's ``$PK`` (before the ``Y=`` line) should *not* be defined using ``stparm`` in PML
   unless they are also associated with a ``fixef`` (and thus represent an estimable parameter – a THETA in NONMEM). If a NONMEM variable is
   assigned a value in ``$PK`` and is *not* a THETA, represent it in PML with a top-level assignment statement, *not* with ``stparm``.

-  **Execution:** Structural parameter statements are executed before
   anything else, except sequence statements to initialize them.
-  **Conditional Logic:** Use the ternary operator (``? :``) for
   conditional logic within ``stparm`` expressions, *not* ``if/else``.
-  **Important Note:** When using time-dependent logic within
   ``stparm``, closed-form solutions are not applicable, and the model
   will rely on a numerical ODE solver.

**Example:**

.. code:: pml

   stparm(V  = tvV * exp(nV))                  // Volume (log-normal)
   stparm(Ka = tvKa)                            // Absorption rate constant (fixed effect)
   stparm(Cl = tvCl * exp(dCldSex1*(Sex==1)) * exp(nCl + nClx0*(Period==1) + nClx1*(Period==2))) // Clearance (log-normal) Example with occasion covariate Period with 2 levels amd categorical covariate Sex with 2 levels

**Keywords:** structural parameter, stparm, parameter, population, fixed effect, random effect, covariate, IIV

**See also:** ``fixef`` Statement, ``ranef`` Statement,
Covariates, Fixed Effects, Random Effects, Log-Normal Distribution, ``if`` and Ternary Operator


fixef
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``fixef`` statement defines fixed-effect parameters
(often called "thetas" in NONMEM), representing the typical or
population values of structural parameters. It also allows specifying
initial estimates, bounds, and enabling/disabling fixed effects for
covariate search.

-  **Purpose:** Defines fixed-effect parameters and their properties.
-  **Syntax:**
   ``fixef(parameter[(freeze)][(enable=c(int))] [= c([lower bound],[ initial estimate],[ upper bound])])``

   -  ``parameter``: The name of the fixed-effect parameter (e.g.,
      ``tvV``, ``tvCl``, ``dCldSex``).
   -  ``freeze``: (Optional) If present, the parameter is *not*
      estimated; it's fixed at its initial estimate.
   -  ``enable=c(int)``: (Optional) Controls whether the parameter is
      considered during *covariate search* procedures (0 = disabled, 1 =
      enabled). Has no effect on a regular model fit.
   -  ``= c([lower bound],[ initial estimate],[ upper bound])]``:
      (Optional) Specifies the lower bound, initial estimate, and upper
      bound. Any of these can be omitted (using commas as placeholders).
      If only one value is given without bounds, it represents the
      initial value

.. note::
  May use ``freeze`` for parameters that are defined and assigned values in the NONMEM ``$PK`` block but are not THETAs (i.e., not estimated),
  but probably it is better to use the direct assignment outside fixef/stparm statements

-  **Default Initial Values:** If no initial estimate is provided:

   -  Covariate effects: Default initial value is 0.
   -  Other fixed effects: Default initial value is 1.

-  **Multiple fixef:** It is possible to have more than one ``fixef`` statement.

**Example:**

.. code:: pml

       fixef(tvV  = c(0, 10, 100))  // Initial estimate 10, bounds [0, 100]
       fixef(tvCl = c(, 5, )) // Initial estimate 5, no bounds
       fixef(dCldSex1(enable=c(0)) = c(, 0, )) // Enabled for covariate search, initial estimate 0

**Keywords:** fixed effect, fixef, population parameter, typical value, initial estimate, bounds, enable

**See also:** ``stparm`` Statement, ``ranef`` Statement, Covariates, Fixed Effects, Bounds, Covariate Search


ranef
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``ranef`` statement defines random-effect parameters
(often called "etas" in NONMEM), representing inter-individual
variability (IIV) in structural parameters. It also defines the
variance-covariance structure of the random effects.

-  **Purpose:** Defines random effects and their variance-covariance
   matrix.

-  **Syntax:** ``ranef(specification)``

   -  ``specification``: Defines the random effects and their
      relationships. Common options include:

      -  ``diag(parameter1, parameter2, ...)``: Diagonal covariance
         matrix (random effects are independent).
      -  ``block(parameter1, parameter2, ...)``: Full covariance matrix
         (random effects can be correlated).
      -  ``same(parameter1, parameter2, ...)``: Specifies that
         parameters share the same variance (and covariance, if within a
         ``block``).
      -  ``= c(...)``: initial estimates for variance/covariance

-  The initial estimates are provided for variance-covariance matrix

-  **Multiple ranef Statements:** A model can have multiple ``ranef`` statements.

-  **NONMEM Equivalent:**

   -  ``diag(nV, nCl)`` is similar to NONMEM's:

   ::

      $OMEGA DIAG
      0.04 ;nV
      0.09 ;nCl

   -  ``block(nV, nCl)`` is similar to NONMEM's:

   ::

      $OMEGA BLOCK(2)
      0.04 ;nV
      0.02 0.09 ;nCl

**Examples:**

.. code:: pml

   ranef(diag(nV, nCl) = c(0.04, 0.09))  // Diagonal covariance: V and Cl vary independently

   ranef(block(nV, nCl) = c(0.04, 0.02, 0.09))  // Full covariance: V and Cl are correlated

   ranef(diag(nV) = c(0.04), diag(nCl) = c(0.09)) // Equivalent to the first example

   ranef(block(nCl1, nCl2) = c(1, 0.5, 2), same(nCl3, nCl4)) //block + same

**Keywords:** random effect, ranef, inter-individual variability, IIV, variance, covariance, omega, diag, block, same

**See also:** ``stparm`` Statement, ``fixef`` Statement, Random Effects, Variance, Covariance, Inter-Individual Variability


Fixed Effects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fixed effects represent the typical or population values of
parameters in the model. They are estimated from the data and are
assumed to be constant across all individuals.

\* Represented by ``fixef`` \* Usually defined with ``tv`` prefix

**Keywords:** fixed effect, population parameter, typical value, theta, fixef

**See also:** ``fixef`` Statement, ``stparm`` Statement, Random Effects


Random Effects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Random effects represent the variability in parameters
*between* individuals. They are assumed to be drawn from a distribution
(usually normal or log-normal) with a mean of zero and an estimated
variance-covariance matrix.

\* Represented by ``ranef`` \* Usually defined with ``n`` prefix

**Keywords:** random effect, inter-individual variability, IIV, eta, ranef, variance, covariance

**See also:** ``ranef`` Statement, ``stparm`` Statement, Fixed Effects, Variance, Covariance, Inter-Individual Variability


Log-Normal Distribution (in Parameter Definitions)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The log-normal distribution is commonly used for parameters
that must be positive (e.g., clearance, volume). It's implemented in
``stparm`` using the ``exp()`` function.

-  **Syntax:** ``parameter = tvParameter * exp(nParameter)``

   -  ``tvParameter``: The typical value (fixed effect).
   -  ``nParameter``: The random effect (normally distributed with mean
      0).
   -  ``exp()``: The exponential function. This ensures that
      ``parameter`` is always positive, regardless of the value of
      ``nParameter``.

-  **Why Log-Normal?** Many pharmacokinetic parameters (e.g., clearance,
   volume) can only have positive values. The log-normal distribution
   guarantees positivity.

**Example:**

.. code:: pml

   stparm(
     Cl = tvCl * exp(nCl)  // Clearance is log-normally distributed
   )

**Keywords:** log-normal, distribution, positive parameter, stparm, exp

**See also:** ``stparm`` Statement, Fixed Effects, Random Effects, Normal Distribution


Normal Distribution (in Parameter Definitions)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The normal distribution can be used for parameters that can
take on both positive and negative values.

-  **Syntax:** ``parameter = tvParameter + nParameter``

**Example:**

.. code:: pml

   stparm(
     Effect = tvEffect + nEffect  // Effect can be positive or negative
   )

**Keywords:** normal, distribution, stparm, additive

**See also:** ``stparm`` statement, Log-Normal Distribution


Bounds (in fixef statements)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bounds (lower and upper limits) can be specified for fixed
effects within the ``fixef`` statement. This constrains the parameter
values during estimation, preventing them from taking on unrealistic
values.

-  **Syntax:**
   ``fixef(parameter = c([lower bound],[ initial estimate],[ upper bound]))``
-  Any value could be skipped

**Example:**

.. code:: pml

   fixef(
     tvCl = c(0, 5, 20)  // Cl must be between 0 and 20, with an initial estimate of 5
   )

**Keywords:** bounds, fixef, lower bound, upper bound, parameter constraints

**See also:** ``fixef`` statement


Covariates
------------------------------------------------------------------------

Covariates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Covariates are variables that can influence the model's
parameters or outcomes. They represent characteristics of the
individuals, their environment, or external influences. PML supports
continuous, categorical, and occasional covariates, any of which can be
time-varying.

-  **Purpose:** To incorporate the effects of individual
   characteristics, external factors, or time-dependent changes on the
   model.
-  **Types of Covariates:**

   -  **Continuous:** Take on a continuous range of numerical values
      (e.g., weight, age, creatinine clearance).
   -  **Categorical:** Take on a limited number of discrete values
      representing categories (e.g., sex, disease status, treatment
      group).
   -  **Occasional:** Represent different occasions or periods *within*
      an individual's data (e.g., different treatment cycles). These are
      inherently time-varying.

-  **Declaration:** Covariates *must* be declared using either the
   ``covariate``, ``fcovariate``, or ``interpolate`` statement.
-  **Time-Varying Behavior:** *Any* type of covariate (continuous,
   categorical, or occasional) can be time-varying. The ``covariate``,
   ``fcovariate``, and ``interpolate`` statements control how the
   covariate values are handled over time.
-  **Usage:** Covariates can be used in:

   -  ``stparm`` statements to model their effects on structural
      parameters.
   -  Expressions within the model (e.g., in ``deriv`` statements or
      likelihood calculations).

-  **Data Mapping:** Covariates are linked to columns in the input
   dataset through *column mappings*. This is typically done in a
   separate file or within the user interface of the modeling software
   (e.g., Phoenix NLME). The correct syntax for mapping is, for example,
   ``covr(wt<-"wt")``.

**Keywords:** covariate, independent variable, predictor, time-varying, categorical, continuous, occasional, fcovariate, covariate, input, data mapping

**See also:** ``covariate`` Statement, ``fcovariate`` Statement,
``interpolate`` Statement, ``stparm`` Statement, Continuous Covariates,
Categorical Covariates, Occasional Covariates, Time-Varying Covariates, Data Mapping


covariate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``covariate`` statement declares a covariate and
specifies that its values should be extrapolated *backward* in time. The
most recent value of the covariate is used until a new value is
encountered.

-  **Syntax:** ``covariate(covariateName)`` or
   ``covariate(covariateName())``

   -  ``covariateName``: The name of the covariate.
   -  ``()``: Empty parentheses are *required* for categorical
      covariates and *recommended* for occasional covariates (though
      technically optional for occasion).

-  **Backward Extrapolation:** The value of the covariate at any given
   time is the *most recent* value observed *before* that time. If no
   value is given at time=0, the first available value is used.

**Example:**

.. code:: pml

   covariate(Weight)  // Declares 'Weight' as a continuous covariate
   covariate(Sex())    // Declares 'Sex' as a categorical covariate

**NONMEM Equivalent:** There is no direct equivalent in NONMEM. NONMEM's default behavior for covariates is backward extrapolation, similar to PML's ``covariate``.

**Keywords:** covariate, backward extrapolation, time-varying covariate

**See also:** Covariates, ``fcovariate`` Statement,
``interpolate`` Statement, Time-Varying Covariates, Categorical Covariates, Occasional Covariates


fcovariate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``fcovariate`` statement declares a covariate and
specifies that its values should be extrapolated *forward* in time. The
current value is used until a new value is encountered. ``fcovariate``
is generally preferred for occasion covariates.

-  **Syntax:** ``fcovariate(covariateName)`` or
   ``fcovariate(covariateName())``

   -  ``covariateName``: The name of the covariate.
   -  ``()``: Empty parentheses are *required* for categorical
      covariates and *recommended* (but technically optional) for
      occasional covariates.

-  **Forward Extrapolation:** The value of the covariate at any given
   time is the value observed *at* that time, and this value is carried
   *forward* until a new value is encountered. The first available value
   is also carried backward if no value is given at time=0.
-  **Occasion Covariates:** ``fcovariate`` is generally preferred for
   *occasion covariates*.

**Example:**

.. code:: pml

   fcovariate(DoseRate)   // Declares 'DoseRate' as a time-varying covariate
   fcovariate(Occasion())  // Declares 'Occasion' as an occasion covariate (recommended)
   fcovariate(Occasion) // also valid, but less explicit

**NONMEM Equivalent:** There's no direct equivalent in NONMEM. You would typically handle forward extrapolation of occasion covariates implicitly
through the structure of your dataset and control stream.

**Keywords:** fcovariate, forward extrapolation, time-varying covariate, occasion covariate

**See also:** Covariates, ``covariate`` Statement, ``interpolate``
Statement, Time-Varying Covariates, Occasional Covariates, Categorical Covariates


interpolate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``interpolate`` statement declares a *continuous*
covariate whose values are linearly interpolated between the time points
at which it is set.

-  **Syntax:** ``interpolate(covariateName)``

   -  ``covariateName``: The name of the covariate.

-  **Linear Interpolation:** The value of the covariate varies linearly
   between the time points at which it is set in time-based models.

-  **Extrapolation:** If no covariate value is given, the latest value
   is carried forward. If no value is given at time=0, the first
   available value is used.

-  **Continuous Covariates Only:** ``interpolate`` can *only* be used
   with *continuous* covariates.

**Example:**

.. code:: pml

   interpolate(InfusionRate)

**NONMEM Equivalent:** There is no direct equivalent in NONMEM. Linear interpolation of covariates is not a built-in feature. You would
typically pre-process your data to create interpolated values if needed.

**Keywords:** interpolate, covariate, linear interpolation, time-varying covariate, continuous covariate

**See also:** Covariates, ``covariate`` Statement, ``fcovariate`` Statement, Time-Varying Covariates, Continuous Covariates


Continuous Covariates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Continuous covariates take on a continuous range of
numerical values. They can be time-varying or constant within an
individual.

-  **Examples:** Weight, age, creatinine clearance, body surface area.
-  **Declaration:** Declared using ``covariate``, ``fcovariate``, or
   ``interpolate``.
-  **Usage:** Used directly in mathematical expressions within
   ``stparm`` statements or other model equations.
-  **Mapping:** ``covr(Wt<-"Wt")``

**Example:**

.. code:: pml

   fcovariate(Weight)  // Weight as a time-varying covariate

   stparm(
     Cl = tvCl * (Weight / 70)^0.75 * exp(nCl)  // Allometric scaling of clearance
   )

**Keywords:** continuous covariate, covariate, numerical, time-varying

**See also:** Covariates, ``covariate`` Statement, ``fcovariate`` Statement, ``interpolate`` Statement, ``stparm`` Statement, Data Mapping


Categorical Covariates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Categorical covariates take on a limited number of discrete
values representing categories. PML requires you to define the mapping
between the data values and category names in the *column definition
file*.

-  **Examples:** Sex (Male/Female), Disease Status (Normal/Mild/Severe),
   Treatment Group (Placebo/Active).
-  **Declaration:** Declared using ``covariate(CovariateName())`` or
   ``fcovariate(CovariateName())``. The empty parentheses ``()`` are
   *required*.
-  **Mapping (Column Definition File):** You *must* map the covariate
   and its categories in the column definition file (or equivalent
   interface in your software).

   -  **With Labels:** If your data file already contains meaningful
      category labels (e.g., "Male", "Female"), map them directly. The
      general NONMEM-style syntax is:
      ``covr(Sex <- "Sex"("Male" = 0, "Female" = 1))  // Example`` This
      maps the "Sex" column in the data to a covariate named ``Sex`` in
      the model, with "Male" coded as 0 and "Female" as 1. The first
      category is used as a reference category.

   -  **Without Labels:** If your data file uses numeric codes (e.g., 0,
      1) without explicit labels, you can define the labels during
      mapping using empty parentheses:
      ``covr(Sex <- "Sex"())  // Example`` In that case the first unique
      value will be used as a reference.

-  **Usage in stparm:** You typically use logical expressions
   ``(CovariateName == value)`` within ``stparm`` statements to model
   the effects of different categories. This creates implicit "dummy
   variables." The first category encountered in the data is treated as
   the *reference category*, and fixed effects for other categories
   represent differences from the reference. Use the ternary operator
   (``? :``) for more complex conditional logic.

**Example (PML code):**

.. code:: pml

   test() {
     fcovariate(Sex())  // Declare Sex as a categorical covariate

     stparm(
       Cl = tvCl * exp(dClSex * (Sex == 1) + nCl)  // Effect of Sex on Cl
     )

     fixef(
       tvCl   = c(, 10, ),
       dClSex = c(, 0, )  // Fixed effect for Sex=1 (relative to Sex=0)
     )

     ranef(diag(nCl) = c(0.25))

     // ... rest of the model ...
   }

**NONMEM Equivalent:** The PML code above is similar to the following in
NONMEM (using abbreviated code):

.. code:: nonmem

   $INPUT ... SEX ...
   $SUBROUTINES ...
   $PK
     TVCL = THETA(1)
     DCLSEX = THETA(2)
     CL = TVCL * EXP(DCLSEX*(SEX.EQ.1) + ETA(1))
   $THETA
    (0, 10) ; TVCL
    (0)      ; DCLSEX
   $OMEGA
    0.25 ; ETA(1) variance (IIV on CL)

**Keywords:** categorical covariate, covariate, discrete, categories, dummy variable, indicator variable, time-varying, data mapping

**See also:** Covariates, ``covariate`` Statement, ``fcovariate`` Statement, ``stparm`` Statement, Fixed Effects, Data Mapping, Dummy Variables, ``if`` and Ternary Operator


Occasion Covariates and Inter-Occasion Variability (IOV)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Occasion covariates represent distinct periods in a
subject's data (e.g., treatment cycles). Their primary use is to model
**Inter-Occasion Variability (IOV)**, which is the random, unpredictable
variability *within a single subject* from one occasion to the next.
This is modeled using **random effects**, not fixed effects.

-  **Concept:** While Inter-Individual Variability (IIV) describes why
   Subject A's average parameter value is different from Subject B's,
   IOV describes why Subject A's parameter value during Occasion 1 is
   different from their own value during Occasion 2.
-  **Declaration:** Always declare the occasion variable, preferably
   with ``fcovariate(Occasion())``. The parentheses ``()`` are
   recommended for clarity.

**Correct Implementation: Modeling IOV with Random Effects**

This is the standard and pharmacokinetically correct approach. It
assumes that a subject's parameter value for a specific occasion is a
random deviation from their overall mean parameter value.

-  **PML Syntax:** You create a separate random effect (``eta``) for
   each occasion level and add it to the structural parameter
   expression.

   -  ``stparm(Param = tvParam * exp( nParam + nParamOcc1*(Occasion==1) + nParamOcc2*(Occasion==2) + ... ))``

-  The term ``nParam`` represents the subject's IIV (their deviation
   from the population typical value ``tvParam``).
-  The terms ``nParamOcc1``, ``nParamOcc2``, etc., represent the IOV
   (the deviation for that specific occasion from the subject's mean).

**Example (IOV on Clearance):**

.. code:: pml

   test() {
     fcovariate(Occasion()) // Assume Occasion has levels 1, 2, 3

     // Cl includes a random effect for IIV (nCl) and separate random effects for IOV on each occasion
     stparm(Cl = tvCl * exp( nCl + nCl_Occ1*(Occasion==1) + nCl_Occ2*(Occasion==2) + nCl_Occ3*(Occasion==3) ))

     fixef(tvCl = c(, 1, ))
     ranef(diag(nCl) = c(1)) // IIV variance on Cl

     // Define the IOV variances. 'same()' is often used to assume variability is equal across occasions.
     ranef(diag(nCl_Occ1) = c(1), same(nCl_Occ2), same(nCl_Occ3))
     ...
   }

**Incorrect Implementation: Modeling Occasions with Fixed Effects**

It is also possible to model an occasion as a fixed effect, but this
answers a different scientific question and is generally not what is
meant by an "occasion effect." A fixed effect tests whether the
*population average* parameter is systematically different on one
occasion versus another (e.g., "Is clearance for *all subjects* 20%
lower on Occasion 2?"). This is a cohort effect, not within-subject
variability.

**Example of an (often incorrect) fixed-effect model:**

.. code:: pml

   // This model tests if the POPULATION mean Cl is different on Occasion 2 vs Occasion 1
   stparm(Cl = tvCl * exp( dCldOcc2*(Occasion==2) ) * exp(nCl))
   fixef(dCldOcc2 = c(, 0, )) // Fixed effect for Occasion 2

**pyDarwin Automation Note:** When searching for IOV on a parameter, the
token should provide two options: one with only the base IIV random
effect, and one that adds the IOV random effects. The token must swap
out both the ``stparm`` expression and the corresponding ``ranef``
block.

**Correct Token Structure for IOV on Clearance (_nCl):**

.. code:: json

   "_nCl": [
       [
           "* exp(nCl)",
           "ranef(diag(nCl) = c(1))"
       ],
       [
           "* exp(nCl + (Occasion==1)*nClOccasionx1 + (Occasion==2)*nClOccasionx2)",
           "ranef(diag(nCl) = c(1))\\n\\tranef(diag(nClOccasionx1) = c(1), same(nClOccasionx2))"
       ]
   ]

This correctly links the structural model change to the necessary change
in the random effects structure.

**Keywords:** occasion covariate, IOV, inter-occasion variability, fcovariate, random effects, fixed effects, within-subject variability

**See also:** ``fcovariate`` Statement, Random Effects, ``ranef`` Statement, Fixed Effects, ``stparm`` Statement, Inter-Individual Variability


Time-Varying Covariates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Time-varying covariates are covariates whose values can
change *within* an individual over time. They are essential for modeling
dynamic processes and external influences that vary during the
observation period. *Any* type of covariate (continuous, categorical, or
occasional) can be time-varying.

-  **Declaration:** Declared using ``covariate``, ``fcovariate``, or
   ``interpolate``. ``fcovariate`` is generally preferred for most
   time-varying covariates, especially for categorical and occasion
   covariates.
-  **Data:** The input data must include multiple records per
   individual, with different time points and corresponding covariate
   values.
-  **Extrapolation:**

   -  ``covariate``: Backward extrapolation.
   -  ``fcovariate``: Forward extrapolation (and backward extrapolation
      for the first value).
   -  ``interpolate``: Linear interpolation between defined points
      (continuous covariates only), forward extrapolation after the last
      defined point.

**Example:**

.. code:: pml

   fcovariate(DoseRate)   // DoseRate can change over time

   stparm(
     Cl = tvCl * exp(dClDoseRate * DoseRate + nCl)  // Clearance depends on DoseRate
   )

   // ... rest of the model ...

**Keywords:** time-varying covariate, covariate, fcovariate, covariate, changing covariate, dynamic covariate

**See also:** Covariates, ``covariate`` Statement, ``fcovariate`` Statement, ``interpolate`` Statement, Continuous Covariates, Categorical Covariates, Occasional Covariates


Structural Model Definition
------------------------------------------------------------------------

deriv
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``deriv`` statement defines an ordinary differential
equation (ODE) in the model. This is used to describe how the amount of
drug (or other quantities) in a compartment changes over time. Models
with ``deriv`` statements are inherently time-based.

-  **Purpose:** To define the rate of change of a state variable
   (typically a compartment amount).
-  **Syntax:** ``deriv(variable = expression)``

   -  ``variable``: The name of the state variable being differentiated
      (e.g., ``A1``, ``Aa``, ``CumHaz``). This variable is often called
      an "integrator variable."
   -  ``expression``: An expression defining the rate of change of the
      variable. This can involve parameters, covariates, other
      variables, and mathematical functions.

-  **Time-Based Models:** If a model contains *any* ``deriv`` statement,
   it is considered a *time-based model*, and the built-in variable
   ``t`` (representing time) is automatically available.
-  **State variable modification** Variables on the left side of deriv
   statements can be modified when the model is stopped
-  **Multiple deriv statements:** A model will typically have
   multiple ``deriv`` statements, one for each compartment or state
   variable being modeled.
-  **Right-hand-side Discontinuity:** The use of ``t`` variable on the
   right-hand-side is discouraged.

**Example:**

.. code:: pml

   deriv(Aa = -Ka * Aa)      // Rate of change of amount in absorption compartment Aa
   deriv(A1 = Ka*Aa -Cl * C)       // Rate of change of amount in compartment A1

**NONMEM Equivalent:** The PML code above is similar to the following
NONMEM code:

.. code:: nonmem

   $DES
   DADT(1) = -KA*A(1)
   DADT(2) = KA*A(1) -CL*A(2)/V

**Keywords:** deriv, differential equation, ODE, integrator, state variable, time-based model, dynamic model

**See also:** Time-Based Models, Compartment Models, ``dosepoint`` Statement, ``urinecpt`` Statement, State Variables


Compartment Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compartment models are a common type of pharmacokinetic
model where the body is represented as a series of interconnected
compartments. Drug movement between compartments is described by
differential equations.

-  **Compartments:** Represent theoretical spaces where the drug
   distributes (e.g., central compartment, peripheral compartment,
   absorption compartment).
-  **Differential Equations:** Describe the rate of change of the amount
   of drug in each compartment.
-  **Parameters:** Define the rates of transfer between compartments and
   elimination from the body (e.g., clearance, volume, rate constants).
-  **Implementation in PML:** Compartment models can be implemented
   using:

   -  ``deriv`` statements (for custom models or when flexibility is
      needed).
   -  ``cfMicro`` or ``cfMacro`` statements (for standard 1, 2, or
      3-compartment models).

**Keywords:** compartment model, compartment, differential equation, PK model, ADVAN

**See also:** ``deriv`` Statement, ``cfMicro`` Statement, ``cfMacro`` Statement, Time-Based Models, Pharmacokinetics


cfMicro
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides an efficient **closed-form (analytical) solution**
for standard compartment models using micro-constants. This statement is
**not compatible** with time-varying parameters and must be replaced by
``deriv`` statements in such cases.

-  **Purpose:** To define a standard one-, two-, or three-compartment
   model without explicitly writing out the differential equations,
   which can improve performance.
-  **Parameterization:** Uses *micro-constants* (e.g., ``Ke``, ``K12``,
   ``K21``).
-  **Syntax:**
   ``cfMicro(A, Ke, [K12, K21], [K13, K31], [first = (Aa = Ka)])``

   -  ``A``: The amount in the central compartment.
   -  ``Ke``: The elimination rate constant.
   -  ``K12``, ``K21``: (Optional) Transfer rate constants for a
      two-compartment model.
   -  ``K13``, ``K31``: (Optional) Transfer rate constants for a
      three-compartment model.
   -  ``first = (Aa = Ka)``: (Optional) Specifies first-order absorption
      from a depot compartment ``Aa`` with absorption rate constant
      ``Ka``.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**CRITICAL LIMITATION: Time-Varying Parameters**

The ``cfMicro`` statement uses a **piecewise closed-form (analytical)
solution**. The fundamental assumption is that model parameters (like
``Cl``, ``V``, ``K12``, etc.) are **constant between time-based events**
(such as doses or changes in covariate values). When an event occurs,
the system re-evaluates the parameters and applies the closed-form
solution for the next interval.

This means ``cfMicro`` **can correctly handle** structural parameters
that depend on time-varying covariates declared with ``covariate`` or
``fcovariate``, as these values change at discrete time points.

For example, a model with ``stparm(Cl = tvCl * (CRCL/100) * exp(nCl))``
and ``covariate(CRCL)`` will work correctly with the following data, as
``Cl`` is constant between t=0, t=2, and t=4:

== ==== === ==== ====
ID TIME AMT Cobs CRCL
== ==== === ==== ====
1  0    100 0    70
1  2    .   80   70
1  4    .   70   60
== ==== === ==== ====

However, this piecewise assumption is violated if a structural parameter
changes **continuously** over time. This happens in two main scenarios:

1. A structural parameter depends on a covariate declared with
   ``interpolate()``.
2. A structural parameter's definition explicitly includes the time
   variable ``t``.

-  **CONSEQUENCE:** Using ``cfMicro`` with continuously time-varying
   parameters will produce **incorrect results** without generating a
   syntax error.
-  **REQUIRED ACTION:** If any model parameter changes continuously with
   time (due to ``interpolate()`` or the use of ``t``), you **MUST** use
   ``deriv`` statements to define the model structure. This forces the
   use of a numerical ODE solver that can correctly handle the dynamic
   parameters.
-  **Stricter Rules for cfMacro and cfMacro1**: These are pure
   closed-form solutions and are more restrictive. They require
   structural parameters to be constant for the entire observation
   interval and do not support time-varying covariates of any kind.

**Example of an INVALID model (due to interpolate):**

.. code:: pml

   test() {
       interpolate(scr) // Makes scr a CONTINUOUSLY time-varying covariate
       stparm(Cl = tvCl + dCldscr * scr) // Cl is now continuously time-varying
       cfMicro(A1, Cl / V) // INVALID: cfMicro cannot handle a continuously time-varying Cl
       ...
   }

**Example of the CORRECT equivalent model:**

.. code:: pml

   test() {
       interpolate(scr) // Continuously time-varying covariate
       stparm(Cl = tvCl + dCldscr * scr) // Cl is continuously time-varying
       deriv(A1 = - (Cl/V) * A1) // CORRECT: Must use deriv statement
       ...
   }

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
  When designing a model search in pyDarwin, if **any** candidate model in your search space includes a time-varying covariate
  effect on a structural parameter, **all** structural model options must be written using ``deriv`` statements. Do not mix ``cfMicro`` and
  ``deriv`` based structural models in the same search if time-varying covariates are involved, as it would be an invalid comparison.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Keywords:** cfMicro, closed-form solution, compartment model, micro-constants, ``deriv``, time-varying covariate, ODE solver

**See also:** ``deriv`` Statement, Compartment Models, ``covariate`` Statement, ``interpolate`` Statement, ``fcovariate`` Statement, Time-Varying Covariates


cfMacro and cfMacro1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``cfMacro`` and ``cfMacro1`` statements provide
closed-form solutions for standard compartment models, parameterized
using *macro-constants* (coefficients and exponents of exponential
terms). ``cfMacro`` offers more options, including a stripping dose.

-  **Purpose:** To define a standard compartment model without
   explicitly writing out the differential equations, using a
   macro-constant parameterization.
-  **cfMacro Syntax:**
   ``cfMacro(A, C, DoseVar, A, Alpha, [B, Beta], [C, Gamma], [strip=StripVar], [first=(Aa=Ka)])``

   -  ``A``: The amount in the central compartment (cannot be referred
      to elsewhere in the model).
   -  ``C``: The *concentration* variable in the model.
   -  ``DoseVar``: A variable to record the initial bolus dose (needed
      for ``idosevar``).
   -  ``A``, ``Alpha``: Macro-constants for the first exponential term.
   -  ``B``, ``Beta``: (Optional) Macro-constants for the second
      exponential term (two-compartment model).
   -  ``C``, ``Gamma``: (Optional) Macro-constants for the third
      exponential term (three-compartment model).
   -  ``strip=StripVar``: (Optional) Specifies a covariate
      (``StripVar``) to provide a "stripping dose" for simulations.
   -  ``first = (Aa = Ka)``: (Optional) Specifies the first order
      absorption

-  **cfMacro1 Syntax:**
   ``cfMacro1(A, Alpha, [B, Beta], [C, Gamma], [first=(Aa=Ka)])``

   -  Simplified version of ``cfMacro``.
   -  ``A``: Amount in the central compartment.
   -  ``Alpha``, ``B``, ``Beta``, ``C``, ``Gamma``: Macro-constants. The
      response to bolus dose is predefined
   -  ``first = (Aa = Ka)``: (Optional) Specifies the first order
      absorption

-  **Stripping Dose:** The ``strip`` option in ``cfMacro`` allows you to
   specify a covariate that provides a "stripping dose" value. This is
   used in simulations to represent the initial dose used when the model
   was originally fit.

**Example (cfMacro with two compartments and stripping dose):**

.. code:: pml

   cfMacro(A1, C1, A1Dose, A, Alpha, B, Beta, strip=A1Strip)
   dosepoint(A1, idosevar = A1Dose)
   covariate(A1Strip)

**Example (cfMacro1 with one compartment):**

.. code:: pml

   cfMacro1(A, Alpha)

**Keywords:** cfMacro, cfMacro1, closed-form solution, compartment model, macro-constants, A, Alpha, B, Beta, C, Gamma, stripping dose

**See also:** Compartment Models, ``deriv`` Statement, ``cfMicro`` Statement, Macro-Constants, Closed-Form Solutions, Pharmacokinetics


.. _title-micro-constants-vs-macro-constants:

Micro-Constants vs. Macro-Constants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compartment models can be parameterized using either
micro-constants (rate constants) or macro-constants (coefficients and
exponents of exponential terms). ``cfMicro`` uses micro-constants, while
``cfMacro`` and ``cfMacro1`` use macro-constants.

-  **Micro-Constants:**

   -  Rate constants that describe the transfer of drug between
      compartments and elimination from the body (e.g., ``Ke``, ``K12``,
      ``K21``).
   -  More directly related to the underlying physiological processes.
   -  Used with ``cfMicro`` and ``deriv`` statements.

-  **Macro-Constants:**

   -  Coefficients and exponents of exponential terms in the closed-form
      solution (e.g., ``A``, ``Alpha``, ``B``, ``Beta``, ``C``,
      ``Gamma``).
   -  Less intuitive from a physiological perspective.
   -  Used with ``cfMacro`` and ``cfMacro1``.

-  **Conversion:** It's possible to convert between micro-constants and
   macro-constants, but the equations can be complex, especially for
   models with more than one compartment.

**Keywords:** micro-constants, macro-constants, Ke, K12, K21, A, Alpha, B, Beta, C, Gamma, parameterization, cfMicro, cfMacro

**See also:** ``cfMicro`` Statement, ``cfMacro`` Statement, ``cfMacro1`` Statement, Compartment Models, Pharmacokinetics


dosepoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``dosepoint`` statement specifies a compartment that
can receive doses (either bolus or infusion). It also allows for options
like lag time, infusion duration/rate, bioavailability, and actions
performed before/after dosing.

-  **Purpose:** To define where doses are administered in the model.

-  **Syntax:**
   ``dosepoint(compartmentName [, tlag = expr][, duration = expr][, rate = expr][, bioavail = expr][, dobefore = sequenceStmt][, doafter = sequenceStmt][, split][, idosevar = variableName][, infdosevar = variableName][, infratevar = variableName])``

   -  ``compartmentName``: The name of the compartment receiving the
      dose.
   -  ``tlag = expr``: (Optional) Time delay before dose delivery.
   -  ``duration = expr``: (Optional) Duration of a zero-order infusion.
   -  ``rate = expr``: (Optional) Rate of a zero-order infusion. Cannot
      be used with ``duration``.
   -  ``bioavail = expr``: (Optional) Bioavailability fraction (0 to 1).
   -  ``dobefore = sequenceStmt``: (Optional) ``sequence`` block
      executed *before* dose delivery.
   -  ``doafter = sequenceStmt``: (Optional) ``sequence`` block executed
      *after* dose delivery (or infusion completion).
   -  ``split``: (Optional, rarely used) For UI compatibility.
   -  ``idosevar = variableName``: (Optional) Captures the value of the
      *first bolus dose*.
   -  ``infdosevar = variableName``: Captures the value of the first
      infusion dose.
   -  ``infratevar = variableName``: (Optional) Captures the *infusion
      rate* of the *first infusion dose*.

-  **Bolus vs. Infusion:**

   -  If neither ``duration`` nor ``rate`` is specified, the dose is
      treated as a bolus (instantaneous).
   -  If ``duration`` or ``rate`` is specified, the dose is treated as a
      zero-order infusion.

-  **Multiple dosepoints:** It is allowed to have several ``dosepoint``
   statements.

-  **dosepoint1 and dosepoint2:**

   -  ``dosepoint1`` is a direct synonym for ``dosepoint``.
   -  ``dosepoint2`` has a special function: it allows defining a
      *second* dosing stream on the *same compartment* that already has
      a ``dosepoint`` or ``dosepoint1`` defined. This is used for models
      where a single dose is split into multiple administration profiles
      (e.g., part bolus, part infusion).
   -  ``split`` argument: When using ``dosepoint`` and
      ``dosepoint2`` on the same compartment to split a single dose
      amount from your data, you **must** add the ``split`` argument to
      the first ``dosepoint`` statement. This tells the system that the
      ``dose()`` and ``dose2()`` mappings in the column definition file
      will both point to the *same data column* (e.g., ``AMT``).

      -  Without ``split``: The system would expect ``dose()`` and
         ``dose2()`` to map to two *different* amount columns (e.g.,
         ``AMT1``, ``AMT2``).
      -  With ``split``: ``dosepoint(Aa, bioavail=0.5, split)`` and
         ``dosepoint2(Aa, bioavail=0.5, ...)`` can both be sourced from
         a single ``AMT`` column.

-  **Advanced Usage: Modeling with Multiple Dosepoints** A powerful
   feature of PML is the ability to use multiple ``dosepoint``
   statements to model complex absorption. If two or more ``dosepoint``
   statements exist, a single dose amount (``AMT``) from the input data
   can be programmatically split between them using the ``bioavail``
   option. The sum of the bioavailability fractions across all active
   pathways for a given dose should typically equal 1. This is the
   foundation for modeling the parallel and sequential absorption
   schemes used for advanced drug formulations.

   **See "Modeling Complex Absorption Schemes" for detailed examples.**

**Example (Bolus dose with lag time):**

.. code:: pml

   dosepoint(Aa, tlag = 0.5)  // Bolus dose to Aa with a 0.5 time unit lag

**Example (Zero-order infusion with bioavailability):**

.. code:: pml

   dosepoint(A1, duration = 2, bioavail = 0.8)  // Infusion to A1 over 2 time units, 80% bioavailability

**Example (Capturing the first bolus dose to use it in the secondary statement):**

.. code:: pml

   dosepoint(A1, idosevar = FirstDose)

.. note::
  A dosepoint statement is REQUIRED for any compartment that receives doses. Without a dosepoint statement, even if
  your input dataset contains AMT values for that compartment, no dosing will occur in the model.

**NONMEM Equivalent:** \* Bolus dose: In NONMEM, you'd typically use the ``AMT`` column in your dataset along with an appropriate ``EVID`` value
(usually 1) to indicate a bolus dose. \* Infusion: In NONMEM, you'd use ``AMT``, ``RATE`` (or ``DUR``), and an ``EVID`` value (usually 4 for
infusions). \* ``tlag``: Similar to NONMEM's ``ALAG`` \* ``bioavail``: Similar to NONMEM's ``F`` \* ``idosevar``, ``infdosevar``,
``infratevar``: There aren't direct NONMEM equivalents. You might use workarounds with additional parameters or data items.

**Keywords:** dosepoint, dose, dosing, bolus, infusion, tlag, duration, rate, bioavail, dobefore, doafter, idosevar, infdosevar, infratevar, split, dosepoint1, dosepoint2

**See also:** Dosing, Bolus Dose, Infusion, Lag Time, Bioavailability, ``sequence`` Block, Compartment Models


urinecpt
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``urinecpt`` statement defines an elimination
compartment, similar to ``deriv``, but with specific behavior during
steady-state dosing: it's ignored.

-  **Purpose:** To model the elimination of drug or a metabolite into an
   accumulating compartment (typically urine).
-  **Syntax:** ``urinecpt(variable = expression [, fe = fractionExp])``

   -  ``variable``: The name of the elimination compartment amount.
   -  ``expression``: Defines the rate of elimination *into* the
      compartment.
   -  ``fe = fractionExp``: (Optional) Specifies fraction excreted

-  **Steady-State Behavior:** The key difference between ``urinecpt``
   and ``deriv`` is that during *steady-state* simulations, the
   ``urinecpt`` statement is *ignored*. This is because, at steady
   state, the amount in the elimination compartment is not relevant to
   the dynamics of the system.
-  **Resetting:** The amount in the compartment could be set to 0 after
   being observed using observe statement and ``doafter`` option.

**Example:**

.. code:: pml

   urinecpt(A0 = Cl * C)  // Elimination compartment, rate proportional to concentration

**NONMEM Equivalent:** There isn't a direct equivalent in NONMEM. You'd often model urine excretion using a regular compartment (``$DES`` or
built-in ``ADVAN`` subroutine) and then, if needed for steady-state calculations, you would manually ensure that the urine compartment's
contribution is handled appropriately (often by not including it in the objective function calculation at steady state).

**Keywords:** urinecpt, elimination compartment, excretion, steady-state

**See also:** ``deriv`` Statement, Compartment Models, Elimination, Steady State


Observation and Error Models
------------------------------------------------------------------------

observe
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``observe`` statement links model predictions to
observed data, defining the residual error structure. Crucially, each
``observe`` statement must include *exactly one* error variable. It also
handles below-quantification-limit (BQL) data.

-  **Purpose:** To connect model-predicted values to observed data and
   define how the model accounts for the difference (residual error)
   between them.

-  **Syntax:**
   ``observe(observedVariable = expression [, bql[ = value]][, actionCode])``

   -  ``observedVariable``: The name of the observed variable (e.g.,
      ``CObs``, ``EObs``, ``Resp``). This variable will be mapped to a
      column in your input data.
   -  ``expression``: Defines the *predicted* value. This expression
      *must* include exactly one error variable (defined using an
      ``error`` statement). The form of this expression, together with
      the ``error`` statement, determines the error model (additive,
      proportional, etc.).
   -  ``bql``: (Optional) Handles below-quantification-limit (BQL) data
      using the M3 method. See the separate entry on "BQL Handling" for
      details.

      -  ``bql``: Uses dynamic LLOQ, requiring a mapped ``CObsBQL``
         column (or equivalent).
      -  ``bql = <value>``: Uses a static LLOQ *value*. **Important:**
         This must be a numeric literal, *not* an expression.

   -  ``actionCode``: (Optional) Allows executing code (``sequence``
      block) before or after the observation (using ``dobefore`` or
      ``doafter``).

-  **Single Error Variable Restriction:** This is a *key difference*
   from NONMEM. PML allows *only one* error variable per ``observe``
   statement. NONMEM allows combining multiple ``EPS`` terms (e.g.,
   ``Y = F*EXP(EPS(1)) + EPS(2)``). In PML, you achieve combined error
   models using specific functional forms within the ``expression``,
   *not* by adding multiple error variables.

-  **Common Error Models (and how to express them in PML):**

   -  **Additive:** ``observe(CObs = C + CEps)``

      -  Observed value (``CObs``) equals the predicted value (``C``)
         plus an error term (``CEps``). The error is constant regardless
         of the prediction's magnitude.

   -  **Proportional:** ``observe(CObs = C * (1 + CEps))`` or
      ``observe(CObs = C * exp(CEps))``

      -  The error is proportional to the predicted value.
         ``C * (1 + CEps)`` is a common approximation. ``C * exp(CEps)``
         is a log-additive form, ensuring positivity.

   -  **Combined Additive and Proportional:** PML provides two main ways
      to express this:

      -  ``additiveMultiplicative`` **(Built-in Form)**:
         ``observe(CObs = C + CEps * sqrt(1 + C^2 * (EMultStdev / sigma())^2))     error(CEps = ...) // Define CEps as usual``
         This form is mathematically equivalent to a combined additive
         and proportional error model and is often preferred for its
         numerical stability. ``EMultStdev`` represents the proportional
         error standard deviation, and ``sigma()`` represents the total
         variance when C=0.
      -  **Using a Mixing Parameter (MixRatio):**
         ``stparm(CMixRatio = tvCMixRatio) // Define a structural parameter     fixef(tvCMixRatio = c(, 0.1, ))  // And its fixed effect     error(CEps = ...)             // Define the error variable     observe(CObs = C + CEps * (1 + C * CMixRatio))``
         This approach is more flexible and allows for easier
         interpretation of the mixing parameter.

   -  **Power:** ``observe(Obs = Pred + (Pred^power)*Eps)``

      -  The error term's magnitude scales with the predicted value
         raised to the power of power.

-  **Multiple observe Statements:** Use separate ``observe``
   statements for *each* observed variable (e.g., one for plasma
   concentration, one for a PD response). Each ``observe`` statement
   defines its *own* observed variable, predicted value, and error
   structure.

**Example (Proportional Error):**

.. code:: pml

   error(CEps = 0.1)  // Define the error variable and its SD
   observe(CObs = C * (1 + CEps)) // Proportional error

**Example (Combined Error - additiveMultiplicative):**

.. code:: pml

   error(CEps = 0.05) // Additive error SD
   observe(CObs = C + CEps * sqrt(1 + C^2*(0.2/sigma())^2))  // Combined, EMultStdev=0.2

**Example (Combined Error - MixRatio):**

.. code:: pml

   stparm(CMixRatio = tvCMixRatio)
   fixef(tvCMixRatio = c(, 0.1, ))
   error(CEps = 0.05)
   observe(CObs = C + CEps * (1 + C * CMixRatio)) // Combined error

**Example (Multiple Observations - PK and PD):**

.. code:: pml

   error(CEps = 0.1)
   observe(CObs = C * (1 + CEps)) // PK observation

   error(EEps = 2)
   observe(EObs = E + EEps)  // PD observation (additive error)

**NONMEM Translation Note:** When translating from NONMEM, remember that PML *cannot* directly combine multiple ``EPS`` terms in a single
``Y = ...`` line. You *must* use PML's built-in combined error forms (``additiveMultiplicative`` or the ``MixRatio`` approach) or define a
custom likelihood using the ``LL`` statement. NONMEM's ``Y = F*EXP(EPS(1)) + EPS(2)`` is *approximated* in PML by the
``additiveMultiplicative`` form, as NONMEM uses a linear approximation for ``EXP(EPS)`` when the variances are small.

**Keywords:** observe, observation, error model, residual error, additive, proportional, combined, additiveMultiplicative, bql, censored data, M3 method

**See also:** ``error`` Statement, Error Models, BQL Handling, ``LL`` Statement, Data Mapping, ``additiveMultiplicative``


error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``error`` statement defines a residual error variable
and its standard deviation. This variable is *required* for use within
an ``observe`` statement.

-  **Purpose:** To declare a residual error variable (often named with
   an "Eps" suffix) and specify its initial standard deviation.
-  **Syntax:** ``error(errorVariable[(freeze)] = standardDeviation)``

   -  ``errorVariable``: The name of the error variable (e.g., ``CEps``,
      ``EEps``). This name *must* be used in the corresponding
      ``observe`` statement.
   -  ``freeze``: (Optional) If present, the standard deviation is
      *fixed* at the given value and *not* estimated.
   -  ``standardDeviation``: A *numeric literal* (e.g., ``0.1``,
      ``2.5``) representing the initial estimate for the standard
      deviation. 

.. note::
  This must be a simple number. It cannot be an expression, a function call (like ``sqrt()``), or a variable.

-  **Default Value:** If the standard deviation is not provided, the
   default value is 1. But not providing it is a bad practice.
-  **Multiple error Statements:** You need one ``error`` statement
   for *each* error variable used in your model (usually one per
   ``observe`` statement).
-  **Recommended placement:** before ``observe`` statement.

**Example:**

.. code:: pml

   error(CEps = 0.1)       // Error variable CEps, SD = 0.1
   error(EEps(freeze) = 5) // Error variable EEps, fixed SD = 5

   // INCORRECT - standardDeviation cannot be an expression:
   // error(CEps = sqrt(0.04))

   // CORRECT - Use the numeric value directly
   error(CEps = 0.2) // Equivalent to sqrt(0.04) - standard deviation, not variance

**Important Notes (CRITICAL)**:

-  Standard Deviation, NOT Variance: The standardDeviation in the error
   statement must be the standard deviation, NOT the variance. If you
   are translating a model from NONMEM, remember that the $SIGMA block
   often defines variances. You must take the square root of the NONMEM
   variance to obtain the correct standard deviation for PML.

   -  Example: If NONMEM has $SIGMA 0.09, the corresponding PML would be
      error(CEps = 0.3) (because the square root of 0.09 is 0.3).

-  Numeric Literal Requirement: The standardDeviation must be a numeric
   literal. It cannot be an expression, a variable, or a function call.

**NONMEM Equivalent:** The ``error`` statement combined with the error
model specification in ``observe`` is conceptually similar to defining
error terms in NONMEM's ``$ERROR`` block (or within
``$PRED``/``$PREDPP``). The ``freeze`` keyword corresponds to fixing the
associated ``SIGMA`` parameter in NONMEM. **Important Difference:**
NONMEM's ``$SIGMA`` represents *variance*, while PML's ``error``
statement *always* expects the *standard deviation*. You *must* take the
square root of the variance from NONMEM's ``$SIGMA`` when translating to
PML's ``error``.

**Keywords:** error, residual error, error variable, epsilon, standard deviation, freeze

**See also:** ``observe`` Statement, Error Models, Residual Error


Error Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Error models describe how the model accounts for the
difference between predicted and observed values. Common models include
additive, proportional, combined, and power.

-  **Purpose:** To quantify the discrepancy between model predictions
   and observations, reflecting measurement error, biological
   variability, and model misspecification.

-  **Common Error Models (Review - with emphasis on PML
   implementation):**

   -  **Additive:** ``Observed = Predicted + Error``

      -  PML: ``observe(Obs = Pred + Eps)``
      -  Error is constant, regardless of prediction.

   -  **Proportional:** ``Observed = Predicted * (1 + Error)`` or
      ``Observed = Predicted * exp(Error)``

      -  PML: ``observe(Obs = Pred * (1 + Eps))`` (approximation) or
         ``observe(Obs = Pred * exp(Eps))`` (log-additive)
      -  Error is proportional to the prediction.

   -  **Log-additive**: ``observe(CObs = C*exp(Eps))``
   -  **Combined Additive and Proportional:**

      -  PML (Preferred - ``additiveMultiplicative``):
         ``observe(CObs = C + CEps * sqrt(1 + C^2 * (EMultStdev / sigma())^2))     error(CEps = ...) // Define CEps as usual``
         Where 'EMultStdev' is proportional error standard deviation,
         and 'sigma()' represents the variance when C=0.
      -  PML (Using ``MixRatio``):
         ``stparm(CMixRatio = tvCMixRatio)     fixef(tvCMixRatio = c(, 0.1, ))     error(CEps = ...)     observe(CObs = C + CEps * (1 + C * CMixRatio))``

   -  **Power:** ``Observed = Predicted + (Predicted^power) * Error``

      -  PML: ``observe(Obs = Pred + (Pred^power)*Eps)``

-  **Choosing an Error Model:** Select a model that reflects how
   variability changes with the magnitude of the predicted value.

**Keywords:** error model, residual error, additive, proportional, combined, additiveMultiplicative, log-additive, power

**See also:** ``observe`` Statement, ``error`` Statement, Residual Error, ``additiveMultiplicative``


BQL Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below Quantification Limit (BQL) data occurs when the true
value is below the assay's detection limit. PML handles BQL data using
the M3 method within the ``observe`` statement.

-  **Problem:** BQL data are *censored*; we only know the value is below
   a limit (the LOQ).
-  **M3 Method:** Standard approach (Beal, 2001). Calculates the
   *probability* of the true value being below the LOQ.
-  **PML Implementation:** The ``observe`` statement's ``bql`` option
   implements the M3 method.
-  **Two Ways to Use bql:**

   -  ``observe(Obs = ..., bql)`` **(Dynamic LOQ):**

      -  Creates a derived column ``ObsBQL`` (e.g., ``CObsBQL``).
      -  *Optionally* map a column to this flag.
      -  ``ObsBQL = 0`` (or missing): Observation is *above* the LOQ.
      -  ``ObsBQL = non-zero``: Observation is *at or below* the LOQ.
         The ``Obs`` value *becomes* the LOQ.
      -  If ``ObsBQL`` is not mapped, then the values in ``Obs`` are
         used.

   -  ``observe(Obs = ..., bql = <value>)`` **(Static LOQ):**

      -  Defines a *fixed* LOQ *value* (numeric literal).
      -  ``Obs`` values less than ``<value>`` are treated as censored.
      -  Mapping ``ObsBQL`` is optional; mapped values override the
         static value.

-  **Mapping:**

   -  ``censor(CObsBQL)``
   -  ``loq(LOQ)``

**Example (Dynamic LOQ):**

.. code:: pml

   error(CEps = 0.1)
   observe(CObs = C * (1 + CEps), bql)  // Dynamic BQL
   // ... and in the column mappings:
   // censor(CObsBQL) // Optional, for explicit BQL flags
   // loq(LOQ)

**Example (Static LOQ):**

.. code:: pml

   error(CEps = 0.1)
   observe(CObs = C * (1 + CEps), bql = 0.05)  // Static LOQ of 0.05

**NONMEM Equivalent:** In NONMEM, you'd use the ``M3`` method.

.. code:: nonmem

   $ERROR
     CP=A(2)/V
     PROP=CP*RUVCV
     ADD=RUVSD
     SD=SQRT(PROP*PROP+ADD*ADD)
   IF (DV.GE.LLOQ) THEN
     F_FLAG=0 ; ELS
     Y=CP + SD*EPS1
   ELSE
     F_FLAG=1 ; LIKELIHOOD
    Y=PHI((LLOQ-CP)/SD))
   ENDIF

**Keywords:** BQL, below quantification limit, censored data, M3 method, observe, bql, CObsBQL, LOQ

**See also:** ``observe`` Statement, Error Models, Censored Data, Data Mapping


Finding Extrema (peak function and alternative methods)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PML provides the ``peak`` function for automatically
finding the maximum (peak) or minimum (trough) values of a model
variable (typically concentration) and the corresponding times. An
alternative, more manual method using conditional logic is also
possible. Both approaches write results to *output tables*.

PML offers two primary methods for identifying and capturing the maximum
(Cmax, Tmax) and minimum (Cmin, Tmin) values of a model variable
(usually concentration, ``C``) over time:

1. **The peak Function (Automatic, with Interpolation):**

   -  **Purpose:** Automatically finds and reports the peak (maximum) or
      trough (minimum) of a specified variable, along with the time at
      which it occurs. Uses Lagrange interpolation for more precise
      estimation.
   -  **Syntax:**
      ``variableName = peak(internalVariableName = expression, [max/min] [, logicalExpression])``

      -  ``variableName``: A user-defined variable name to store the
         *time* of the extremum (e.g., ``Tmax``, ``Tmin``). This
         variable will be written to the output table.
      -  ``internalVariableName``: A user-defined variable to store the
         value. It is used internally by the ``peak()`` function and
         *should not be declared anywhere else*.
      -  ``expression``: The expression to track (usually the
         concentration, ``C``).
      -  ``max/min``: (Optional) Specifies whether to find the maximum
         (``max``, default) or minimum (``min``).
      -  ``logicalExpression``: (Optional) A logical expression (e.g.,
         ``t < 6``) that restricts the search. If the expression is
         *true*, the function searches for a peak/trough as specified.
         If *false*, it searches for the *opposite* (trough if ``max``,
         peak if ``min``).

   -  **Behavior:**

      -  **Initialization:** Before the first peak/trough is found (or
         after a ``peakreset``), the output variables (``variableName``
         and the ``internalVariableName`` ) will be blank (missing) in
         the output table.
      -  **Detection:** The ``peak`` function continuously monitors the
         ``expression`` and uses a 4-point window to detect potential
         extrema. It uses Lagrange interpolation on these points to
         estimate the precise time and value of the peak/trough.
      -  **Updating:** Once a peak/trough is found, the ``variableName``
         (time) and corresponding value are written to the output table.
         Subsequent peaks/troughs will *only* update these values if
         they are higher/lower (for max/min, respectively) than the
         previously found extremum.
      -  If the optional logical expression is defined, the extremum is
         updated only when the logical expression holds true.
      -  ``peakreset``: The ``peakreset(internalVariableName)`` function resets the internal state of the ``peak`` function,
         causing it to start searching for a new extremum from that point forward. This is crucial for finding multiple
         peaks/troughs within a simulation. It is used in the ``sequence`` block.

   -  **Restrictions:**

      -  Use only in the main model block, *not* in ``sequence``, ``dobefore``, or ``doafter`` blocks.

   **Example (Finding Cmax and Tmax):**

   .. code:: pml

      Tmax = peak(Cmax = C, max) // Find the maximum concentration (Cmax) and its time (Tmax)

   **Example (Finding Cmin and Tmin within a specific time window):**

   .. code:: pml

      Tmin = peak(Cmin = C, min = (t >= 44 and t <= 52)) // Find minimum between t=44 and t=52

   **Example (Multiple peaks, using peakreset):**

   .. code:: pml

      sequence {
        sleep(44)  // Wait until the start of the interval of interest
        peakreset(Cmax) // Reset Cmax search
        peakreset(Cmin) // Reset Cmin search
        sleep(8)   // Observe for 8 time units
        peakreset(Cmax)
        peakreset(Cmin)
      }

      Tmax = peak(Cmax = C, max)
      Tmin = peak(Cmin = C, min)

   **Caution:** The ``peak`` function uses cubic spline interpolation,
   which can be sensitive to discontinuities (e.g., at the start/end of
   an IV infusion). Ensure sufficient simulation output density around
   potential extrema for accurate results.

2. **Manual Method (Using Conditional Logic):**

   -  **Purpose:** Provides more control over the extremum-finding
      process but requires more manual coding.
   -  **Method:** Use assignment statements and the ``max`` and ``min``
      functions within the main model block, combined with the ternary
      operator (``? :``) to track the highest/lowest values and
      corresponding times. *All variables used with this method must be
      initialized appropriately.*

      -  Initialize ``Cmax1`` to a low value that is guaranteed to be
         exceeded, e.g. -1e6
      -  Initialize ``Cmin1``\ to a high value, e.g., 1E6.
      -  Use ``max(current_value, previous_max)`` to update the maximum.
      -  Use ``min(current_value, previous_min)`` to update the minimum.
      -  Use the ternary operator to update the time (``Tmax1``,
         ``Tmin1``) only when a new extremum is found.

   -  **Important:** Unlike with the ``peak`` function, you must
      initialize the variables used to store the maximum and minimum
      values.

   **Example (Finding Cmax and Tmax manually):**

   .. code:: pml

      real(Cmax1, Tmax1, Cmin1, Tmin1)

      sequence{
          Cmax1 = -1E6
          Cmin1 = 1E6
      }

      Cmax1 = max(C, Cmax1)
      Tmax1 = (C == Cmax1 ? t : Tmax1)  // Update Tmax1 only when C equals the current Cmax1
      Cmin1 = C > 0 ? min(C, Cmin1) : 1E6 // use some big value until initialization
      Tmin1 = C == Cmin1 ? t : Tmin1

   **Advantages of Manual Method:** Greater control, potentially more
   robust in some situations with discontinuities (if carefully
   implemented). **Disadvantages of Manual Method:** More code, requires
   careful initialization, no built-in interpolation.

**Key Differences Summarized:**

+-----------------+------------------------+------------------------+
| Feature         | ``peak`` Function      | Manual Method          |
+=================+========================+========================+
| Initialization  | Automatic (blanks      | *Manual* (must         |
|                 | until first extremum)  | initialize Cmax1/Cmin1 |
|                 |                        | to appropriate         |
|                 |                        | low/high values)       |
+-----------------+------------------------+------------------------+
| Interpolation   | Yes (Lagrange)         | No                     |
+-----------------+------------------------+------------------------+
| Resetting       | ``peakreset(i          | Manual logic           |
|                 | nternalVariableName)`` | (typically             |
|                 |                        | re-initializing in a   |
|                 |                        | ``sequence`` block)    |
+-----------------+------------------------+------------------------+
| Code Complexity | Less                   | More                   |
+-----------------+------------------------+------------------------+
| Control         | Less                   | More                   |
+-----------------+------------------------+------------------------+
| Discontinuities | Potentially sensitive  | Can be more robust if  |
|                 | (ensure sufficient     | handled carefully      |
|                 | output density)        |                        |
+-----------------+------------------------+------------------------+
| Where to Use    | Main model block (not  | Main model block       |
|                 | in ``sequence``,       | (variables must be     |
|                 | ``dobefore``, or       | declared with ``real`` |
|                 | ``doafter``).          | or ``double`` if       |
|                 |                        | modified within        |
|                 |                        | ``sequence``).         |
+-----------------+------------------------+------------------------+
| Output          | Table Only             | Table Only             |
+-----------------+------------------------+------------------------+

**NONMEM Equivalent:** There's no direct equivalent to PML's ``peak`` function in NONMEM. NONMEM users typically implement custom code in
``$PRED`` or ``$PK`` to find extrema, similar to the "Manual Method" described above. NONMEM does *not* have built-in Lagrange interpolation
for this purpose.

**Keywords:** peak, trough, Cmax, Tmax, Cmin, Tmin, extremum, maximum, minimum, Lagrange interpolation, ``peakreset``, table, output, simulation


Table Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``table`` statement, defined in the *column definition
file* (or equivalent interface), specifies which variables and events
should be included in the output table(s) generated by a PML model run.

-  **Purpose:** To control the generation of output tables containing
   simulation results, observed data, and other model-related
   information.

-  **Location:** The ``table`` statement is *not* part of the PML code
   itself. It's defined in the *column definition file* (or equivalent
   interface) used by the modeling software (e.g., Phoenix NLME).

-  **Syntax:**

   ::

      table(
        [optionalFile]
        [optionalDosepoints]
        [optionalCovariates]
        [optionalObservations]
        [optionalTimes]
        variableList
      )

   -  ``optionalFile``: Specifies the output file name (e.g.,
      ``file="results.csv"``). If omitted, a default file name is used.
   -  ``optionalDosepoints``: Specifies that output should be generated
      at times when doses are administered to specific compartments
      (e.g., ``dose(A1, Aa)``).
   -  ``optionalCovariates``: Specifies that output should be generated
      when the values of specified covariates change (e.g.,
      ``covr(Weight, Sex)``).
   -  ``optionalObservations``: Specifies that output should be
      generated at times when specific observations are made (e.g.,
      ``obs(CObs, EObs)``).
   -  ``optionalTimes``: Specifies explicit time points for output
      generation. Can include:

      -  Individual time points: ``time(0, 1, 2.5, 5)``
      -  Sequences: ``time(seq(0, 10, 0.1))`` (generates 0, 0.1, 0.2,
         ..., 9.9, 10)
      -  Combinations: ``time(0, seq(1, 5, 0.5), 10)``

   -  ``variableList``: A comma-separated list of variables to include
      in the table. This can include:

      -  Observed variables (``CObs``, ``EObs``, etc.)
      -  Predicted variables (``C``, ``E``, etc.)
      -  Covariates (``Weight``, ``Sex``, etc.)
      -  Model parameters (fixed effects, *but not structural parameters
         directly*)
      -  Secondary parameters
      -  User-defined variables for tracking extrema (e.g., ``Tmax``,
         ``Cmax`` from the ``peak`` function, or ``Tmax1``, ``Cmax1``
         from the manual method)
      -  Time (``t`` or mapped time variable)
      -  Other derived variables

-  **Multiple Tables:** You can define multiple ``table`` statements to
   generate different output tables with different contents and time
   points.

**Example:**

::

   table(file="results.csv",
         time(0, seq(1, 24, 0.5), 48),  // Output at t=0, every 0.5 from 1 to 24, and at t=48
         dose(A1),                      // Output at dose times to compartment A1
         obs(CObs),                   // Output at observation times for CObs
         covr(Weight),                // Output when Weight changes
         C, CObs, Tmax, Cmax, Tmin, Cmin  // Include these variables
        )

   table(file="covariates.csv",
         time(seq(0,24, 4)),
         covr(Weight, Sex),
         Weight, Sex, Age
   )

This defines two tables:

1. ``results.csv``: Contains the predicted concentration (``C``),
   observed concentration (``CObs``), time of maximum concentration
   (``Tmax``), maximum concentration (``Cmax``), time of minimum
   concentration (``Tmin``) and minimum concentration (``Cmin``) ,
   generated at specified times, dose times, observation times, and when
   ``Weight`` changes.
2. ``covariates.csv``: Contains Weight, Sex and Age generated at
   specified times and when ``Weight`` or ``Sex``\ changes.

**Important Notes:**

-  The ``table`` statement controls *output*, not the model's internal
   calculations.
-  The order of variables in the ``variableList`` determines the order
   of columns in the output table.
-  Time points specified in ``optionalTimes`` are automatically sorted.
-  Variables like ``Tmax``, ``Cmax`` (from ``peak`` function or manual
   method) should be added in output *tables*, not in ``secondary``
   statements.

**Keywords:** table, output, results, csv, data, time points, dosepoints, covariates, observations, ``seq``


Delays
------------------------------------------------------------------------

delay Function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``delay`` function introduces a time delay into a
model. It can represent either a discrete delay (all signal mediators
have the same delay) or a distributed delay (delay times follow a
distribution), modeling processes with a time lag.

-  **Purpose:** To model time delays, either discrete or distributed, in
   a dynamic system.
-  **Syntax:**
   ``delay(S, MeanDelayTime [, shape = ShapeParam][, hist = HistExpression][, dist = NameOfDistribution])``

   -  ``S``: The signal (expression) to be delayed. *Cannot directly
      depend on dose-related inputs*.
   -  ``MeanDelayTime``: The mean delay time.
   -  ``shape = ShapeParam``: (Optional) Shape parameter for the
      distribution (distributed delay). Interpretation depends on
      ``dist``:

      -  ``dist = Gamma`` or ``dist = Weibull``: ``ShapeParam`` is the
         shape parameter *minus 1*. Must be non-negative.
      -  ``dist = InverseGaussian``: ``ShapeParam`` is the shape
         parameter itself.

   -  ``hist = HistExpression``: (Optional) The value of ``S`` *before*
      time 0 (the "history function"). If not provided, ``S`` is assumed
      to be 0 before time 0.
   -  ``dist = NameOfDistribution``: (Optional) The distribution:
      ``Gamma`` (default), ``Weibull``, or ``InverseGaussian``.

-  **Discrete vs. Distributed Delay:**

   -  If ``shape`` is *not* provided, a *discrete* delay is used:
      ``S(t - MeanDelayTime)``.
   -  If ``shape`` *is* provided, a *distributed* delay is used
      (convolution of ``S`` with the distribution's PDF).

-  **Limitations:**

   -  Cannot be used with closed-form solutions (``cfMicro``,
      ``cfMacro``) or matrix exponentiation.
   -  ``S`` cannot directly depend on dose-related inputs. Use
      ``delayInfCpt`` for absorption delays.
   -  Should be used sparingly

**Example (Discrete Delay):**

.. code:: pml

   deriv(A = -k * delay(A, 2, hist = 10))  // A is delayed by 2 time units, initial value 10
   sequence {A=10}

**Example (Distributed Delay - Gamma):**

.. code:: pml

   deriv(A = -k * delay(A, 5, shape = 2, hist = 0, dist = Gamma)) // Gamma-distributed delay

**NONMEM Equivalent:** There is no direct single-function equivalent in NONMEM. Delays, especially distributed delays, often require custom
coding in NONMEM using differential equations or user-defined subroutines.

**Keywords:** delay, delay function, discrete delay, distributed delay, time delay, DDE, delay differential equation, gamma, Weibull, inverse Gaussian, hist

**See also:** Time Delays, Distributed Delays, ``gammaDelay`` Function, ``delayInfCpt`` Statement, Differential Equations


gammaDelay Function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``gammaDelay`` function models a gamma-distributed
delay using an ODE approximation, which can be faster than the ``delay``
function for complex models.

-  **Purpose:** Efficiently model a delay where the delay time follows a
   gamma distribution.
-  **Syntax:**
   ``gammaDelay(S, MeanDelayTime, shape = ShapeParam, [, hist = HistExpression], numODE = NumberOfODEUsed)``

   -  ``S``: The signal to be delayed.
   -  ``MeanDelayTime``: The mean of the gamma distribution.
   -  ``shape = ShapeParam``: The shape parameter of the gamma
      distribution. *Not* shape parameter minus one, unlike ``delay``.
   -  ``hist = HistExpression``: (Optional) Value of ``S`` before time
      0. Defaults to 0.
   -  ``numODE = NumberOfODEUsed``: (Required) Number of ODEs for the
      approximation. Higher values are more accurate but slower. Maximum
      value is 400.

-  **ODE Approximation:** ``gammaDelay`` approximates the convolution
   integral with a system of ODEs.
-  **Accuracy and Performance:** Accuracy depends on ``numODE``.

   -  ``ShapeParam > 1``: Use at least 21 ODEs.
   -  ``ShapeParam <= 1``: Use at least 101 ODEs.

-  **Advantages over delay:** ``gammaDelay`` can be significantly faster than ``delay(..., dist=Gamma)``.
-  **Limitations:**

   -  Only for gamma-distributed delays.
   -  The signal to be delayed cannot depend directly on dose inputs

**Example:**

.. code:: pml

   deriv(A = -k * gammaDelay(A, 5, shape = 3, numODE = 30))  // Gamma-distributed delay
   sequence {A=10}

**NONMEM Equivalent:** There's no direct equivalent in NONMEM. You'd typically implement a gamma-distributed delay using a series of transit
compartments, which approximates a gamma distribution.

**Keywords:** gammaDelay, distributed delay, gamma distribution, approximation, ODE approximation, shape parameter

**See also:** ``delay`` Function, Distributed Delays, Gamma Distribution, ODE Approximation


delayInfCpt
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``delayInfCpt`` statement models a distributed delay
*specifically for input into a compartment*. This is the correct way to
model absorption delays with a distributed delay time.

-  **Purpose:** Model distributed delays in the *absorption* process (or
   any input into a compartment). Necessary because ``delay`` cannot
   handle dose-related inputs directly.
-  **Syntax:**
   ``delayInfCpt(A, MeanDelayTime, ParamRelatedToShape [, in = inflow][, out = outflow][, dist = NameOfDistribution])``

   -  ``A``: The compartment receiving the delayed input. *Can* receive
      doses via ``dosepoint``.
   -  ``MeanDelayTime``: Mean of the delay time distribution.
   -  ``ParamRelatedToShape``: Related to the shape parameter. Depends
      on ``dist``:

      -  ``dist = InverseGaussian``: ``ParamRelatedToShape`` is the
         shape parameter.
      -  ``dist = Gamma`` or ``dist = Weibull``: ``ParamRelatedToShape``
         is the shape parameter *minus 1*. Must be non-negative.

   -  ``in = inflow``: (Optional) Additional inflow *into* compartment
      ``A`` that should also be delayed.
   -  ``out = outflow``: (Optional) Outflow *from* compartment ``A``
      that should *not* be delayed.
   -  ``dist = NameOfDistribution``: (Optional) Delay time distribution:
      ``Gamma`` (default), ``Weibull``, or ``InverseGaussian``.

-  **Relationship to dosepoint:** Used *with* a ``dosepoint`` statement for compartment ``A``. ``dosepoint`` handles dosing, ``delayInfCpt`` models the delay.
-  **History function:** is assumed to be zero

**Example (One-compartment model with gamma-distributed absorption delay):**

.. code:: pml

   delayInfCpt(A1, MeanDelayTime, ShapeParamMinusOne, out = -Cl * C)
   dosepoint(A1)
   C = A1 / V

**Example (Two-compartment model, two absorption pathways, each with
gamma delay):**

.. code:: pml

   delayInfCpt(Ac1, MeanDelayTime1, ShapeParamMinusOne1, out = -Cl * C - Cl2 * (C - C2))
   dosepoint(Ac1, bioavail = frac)  // Fraction 'frac' goes through pathway 1
   delayInfCpt(Ac2, MeanDelayTime2, ShapeParamMinusOne2)
   dosepoint(Ac2, bioavail = 1 - frac) // Remaining fraction goes through pathway 2
   deriv(A2 = Cl2 * (C - C2))
   C = (Ac1 + Ac2) / V
   C2 = A2 / V2

**NONMEM Equivalent:** There isn't a single, direct equivalent in NONMEM. You would likely use a combination of:

-  An absorption compartment.
-  A series of transit compartments (to approximate a distributed delay, particularly a gamma distribution).
-  Potentially, user-defined subroutines (for more complex delay distributions).

**Keywords:** delayInfCpt, absorption delay, distributed delay, compartment, dosepoint, inflow, outflow, gamma, Weibull, inverse Gaussian

**See also:** Absorption Delay, Distributed Delays, ``delay`` Function, ``gammaDelay`` Function, ``dosepoint`` Statement, Compartment Models

transit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``transit`` statement models the flow of material
through a series of linked compartments.

-  **Purpose:** ``transit`` statement can be used to model    the flow of material through a series of linked compartments

-  **Syntax:** ``transit(dest, source, mtt, num [, in = inflow] [, out = outflow])``

   -  ``dest``: destination compartment
   -  ``source``: source compartment, could be a dosepoint
   -  ``mtt``: mean transit time
   -  ``num``: number of transit compartments
   -  ``in = inflow``: (Optional) Specifies any additional inflow into destination compartment
   -  ``out = outflow``: (Optional) Specifies any outflow from destination compartment

-  **Restrictions:** Cannot be used in a model with any closed-form statement

**Example:**

.. code:: pml

   transit(A1, A0, mtt, num, out = - Cl * A1/V)

**NONMEM Equivalent:** The transit statement is conceptually similar to setting up a series of compartments with first-order transfer between
them in NONMEM, but it handles the underlying equations more implicitly.

**Keywords:** transit compartment, absorption

**See also:** Compartment Models


Built-In Functions
------------------------------------------------------------------------

Built-In Mathematical Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PML provides a wide range of standard mathematical
functions that can be used in expressions within the model. These
functions operate on double-precision floating-point numbers.

-  **Common Functions:**

   -  ``sqrt(x)``: Square root of ``x``.
   -  ``exp(x)``: Exponential function (e^x).
   -  ``log(x)``: Natural logarithm (base e) of ``x``.
   -  ``log10(x)``: Base-10 logarithm of ``x``.
   -  ``pow(x, y)``: ``x`` raised to the power of ``y`` (x^y).
   -  ``abs(x)``: Absolute value of ``x``.
   -  ``min(x, y)``: Minimum of ``x`` and ``y``.
   -  ``max(x, y)``: Maximum of ``x`` and ``y``.
   -  ``mod(x, y)``: Remainder of ``x`` divided by ``y`` (modulo operation).
   -  ``sin(x)``, ``cos(x)``, ``tan(x)``: Trigonometric functions (input in radians).
   -  ``asin(x)``, ``acos(x)``, ``atan(x)``: Inverse trigonometric functions (output in radians).
   -  ``sinh(x)``, ``cosh(x)``, ``tanh(x)``: Hyperbolic functions.
   -  ``asinh(x)``, ``acosh(x)``, ``atanh(x)``: Inverse hyperbolic functions.

**Example:**

.. code:: pml

   stparm(
     Cl = tvCl * exp(nCl),
     V  = tvV * exp(nV),
     Ka = tvKa,
     F  = ilogit(tvF)    // Example of using ilogit
   )
   C = A / V
   Rate = Cl * C
   Halflife = log(2) / (Cl / V)  // Calculate half-life using log and division

**Keywords:** mathematical functions, sqrt, exp, log, log10, pow, abs, min, max, mod, sin, cos, tan, asin, acos, atan, sinh, cosh, tanh, asinh, acosh, atanh

**See also:** Expressions, ``stparm`` Statement, ``deriv`` Statement


Link and Inverse Link Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Link and inverse link functions transform variables, often
to constrain them to a specific range (e.g., probabilities between 0 and
1). They are important for modeling categorical/ordinal data.

-  **Purpose:** To relate a linear predictor (which can be any real
   number) to a parameter that has constraints (e.g., a probability).
-  **Common Functions:**

   -  ``ilogit(x)``: Inverse logit function (sigmoid function). Calculates ``exp(x) / (1 + exp(x))``. Transforms any real number ``x`` to a value between 0 and 1 (a probability).
   -  ``logit``: Not directly available as a named function, use ``log(p/(1-p))``.
   -  ``probit(p)``: The probit function.
   -  ``iprobit(x)``: Inverse probit function. Equivalent to ``phi(x)`` (CDF of the standard normal distribution).
   -  ``iloglog(x)``: Inverse log-log link function.
   -  ``icloglog(x)``: Inverse complementary log-log link function.

**Example (Logistic Regression):**

.. code:: pml

   stparm(p = ilogit(A * time + B))  // 'p' is a probability between 0 and 1
   LL(Resp, Resp * log(p) + (1 - Resp) * log(1 - p))

**Keywords:** link function, inverse link function, ilogit, logit, probit, iprobit, iloglog, icloglog, logistic regression, categorical data

**See also:** ``multi`` Statement, ``LL`` Statement, Categorical Data, Ordinal Data, Logistic Regression


if and Ternary Operator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Conditional logic allows different calculations or actions
based on variable values. PML provides ``if/else`` *within* ``sequence``
blocks and the ternary operator (``? :``) for expressions.

-  ``if/else`` **(within** ``sequence`` **blocks ONLY):**

   -  **Syntax:**
      ``sequence { if (condition) { <statements> } else { <statements> } }``
   -  ``condition``: A logical expression (true or false). Use C++-style logical operators (``&&``, ``||``, ``!``) within the condition.
   -  *Only* usable within ``sequence`` blocks.

-  **Restrictions**

   -  if/else could be used inside ``sequence`` blocks only
   -  The observed variable in the ``LL`` statement cannot be used
      anywhere in the model outside of this statement.

-  **Ternary Operator (for expressions):**

   -  **Syntax:** ``condition ? value_if_true : value_if_false``

   -  ``condition``: A logical expression. Use nested ternary operators
      for complex conditions (cannot use ``and``, ``or``, ``not``).

   -  ``value_if_true``: Value if ``condition`` is true.

   -  ``value_if_false``: Value if ``condition`` is false.

   -  Usable *anywhere* an expression is allowed (e.g., ``stparm``, ``deriv``, ``observe``, ``LL``).

   -  For complex conditions (more than one ``else``), nest ternary operators. You cannot use ``and``, ``or``, and ``not`` keywords.
      Use C++ style operators: ``&&``, ``||`` and ``!``.

.. note::
    This is the only way to express conditional logic outside of a ``sequence`` block.


**Example:**

.. code:: pml

     // CORRECT - Ternary operator outside of sequence block
     EHC = SINE <= 0 ? 0 : SINE

     // INCORRECT - if/else outside of sequence block
     EHC = if (SINE <= 0) 0 else SINE

     sequence {
     // CORRECT - if/else inside sequence block
     if (Time > 10)
     {
       DoseRate = 0
       }
     }

**Example (Ternary Operator):**

.. code:: pml

   stparm(
     Cl = tvCl * exp(dClSex * (Sex == 1 ? 1 : 0) + nCl)  // Effect of Sex on Cl
   )

This is equivalent to: If Sex equal to 1 then Cl = tvCl \* exp(nClPeriod2 + nCl) otherwise Cl = tvCl \* exp(nCl)

**Keywords:** if, else, ternary operator, conditional logic, sequence

**See also:** ``sequence`` Block, Expressions, Logical Operators


Logical Operators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Logical operators create logical expressions (conditions)
that evaluate to true or false. The allowed operators differ depending
on whether they are used inside or outside a ``sequence`` block.

-  **Comparison Operators:**

   -  ``==``: Equal to
   -  ``!=``: Not equal to
   -  ``>``: Greater than
   -  ``<``: Less than
   -  ``>=``: Greater than or equal to
   -  ``<=``: Less than or equal to

-  **Logical Operators:**

   -  **Within** ``sequence`` **blocks:** Use C++-style logical operators: ``&&`` (and), ``||`` (or), ``!`` (not).
   -  **Outside** ``sequence`` **blocks:** Nested ternary operators (``? :``) for conditional logic are preferred, but C++-style
      logical operators are also permitted.

**Example:**

.. code:: pml

   sequence {
     if (Time > 10 && DoseRate > 0) {  // Correct
       DoseRate = 0
     }
   }

   stparm(
     K21 = t < 6 ? 0 : t < 8 ? tvK21 : 0  // Correct: Nested ternary
   )

   stparm(
     Cl = tvCl * exp(dClSex * (Sex == 1) + nCl)  // Using == for comparison
   )

   stparm(
     K21 = t >= 6 and t <= 8 ? tvK21 : 0  // INCORRECT: Cannot use 'and'
   )

**Keywords:** logical operators, comparison operators, ==, !=, >, <, >=, <=, and, or, not

**See also:** ``if`` and Ternary Operator, ``sequence`` Block, Expressions


sleep Function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``sleep`` function, used *within* a ``sequence`` block,
pauses execution for a specified duration, introducing time delays in
action code.

-  **Purpose:** To pause the execution of a ``sequence`` block.
-  **Syntax:** ``sleep(duration)``

   -  ``duration``: Expression for the amount of time to sleep (in model
      time units).

-  ``sequence`` **Block Only:** ``sleep`` can *only* be used within a ``sequence`` block.
-  **Relative Time:** ``duration`` is *relative* to when ``sleep`` is
   encountered, *not* absolute time.
-  **Stability:** sleep statement should be used to ensure the stability
   of the algorithms

**Example:**

.. code:: pml

   sequence {
     sleep(5)     // Pause for 5 time units
     A1 = A1 + 10  // Add 10 to compartment A1 after the delay
   }

**Keywords:** sleep, sequence, time delay, action code

**See also:** ``sequence`` Block, Time Delays, Action Code


Statistical Distribution Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PML provides functions for calculating the PDF, CDF, log
PDF, and log CDF of several common statistical distributions, often used
within the ``LL`` statement.

-  **Normal Distribution:**

   -  ``lnorm(x, std)``: Logarithm of the PDF of a normal distribution
      (mean 0, standard deviation ``std``).
   -  ``lphi(x, std)``: Logarithm of the CDF of a normal distribution
      (mean 0, standard deviation ``std``).
   -  ``phi(x)``: CDF of the *standard* normal distribution (mean 0,
      standard deviation 1).

-  **Weibull Distribution:**

   -  ``dweibull(x, shape, scale)``: PDF.
   -  ``ldweibull(x, shape, scale)``: Log PDF.
   -  ``pweibull(x, shape, scale)``: CDF.
   -  ``lpweibull(x, shape, scale)``: Log CDF.

-  **Inverse Gaussian Distribution:**

   -  ``dinvgauss(t, mean, shape)``: PDF.
   -  ``ldinvgauss(t, mean, shape)``: Log PDF.
   -  ``pinvgauss(t, mean, shape)``: CDF.
   -  ``lpinvgauss(t, mean, shape)``: Log CDF.

-  **Poisson Distribution:**

   -  ``lpois(mean, n)``: Logarithm of the probability mass function.
   -  ``ppois(mean, n)``: Probability mass function.
   -  ``rpois(lambda)``: random number
   -  unifToPoisson(mean, r): convert a uniform random number between 0
      and 1 to a Poisson random number

-  **Negative Binomial Distribution:**

   -  lnegbin_rp(r, p, y): logarithm of the probability mass function of
      a negative binomial, distribution parameterized by r and p
   -  megnin_rp(r, p): generate a random sample from a negative binomial
      distribution parameterized by r and p
   -  lnegbin(mean, beta, power, y): logarithm of the probability mass
      function of a negative binomial distribution parameterized by
      mean, beta (=log(alpha)), and power
   -  pnegbin(mean, beta, power, y): probability mass function of a
      negative binomial distribution parameterized by mean, beta (=
      log(alpha)), and power
   -  rnegbin(mean, beta, power): generate a random sample from a
      negative binomial distribution parameterized by mean beta (=
      log(alpha)), and power

**Example (using** ``lnorm`` **in an** ``LL`` **statement):**

.. code:: pml

   LL(Obs, lnorm(Obs - Pred, ErrorSD))  // Custom log-likelihood for normal distribution

**Keywords:** statistical distributions, probability density function,
PDF, cumulative distribution function, CDF, log-likelihood, lnorm, lphi,
phi, dweibull, ldweibull, pweibull, lpweibull, dinvgauss, ldinvgauss,
pinvgauss, lpinvgauss

**See also:** Probability Distributions, ``LL`` Statement, Likelihood


Additional Statements and Features
------------------------------------------------------------------------

Secondary Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Secondary parameters are quantities **calculated** from primary (structural) parameters, fixed effects, and other variables.
They are not directly estimated but are derived. They **cannot** depend directly on structural parameters.

-  **Purpose:** To calculate and report derived quantities of interest (e.g., half-life, AUC, Cmax), **after** the main model fitting is complete.
   **These are not part of the core model dynamics.**
-  **Syntax:** ``secondary(parameterName = expression)``

   -  ``parameterName``: The name of the secondary parameter.
   -  ``expression``: Defines how to calculate ``parameterName``. Can
      include:

      -  Fixed effects (e.g., ``tvV``, ``tvCl``).
      -  Other secondary parameters (defined *before* this one).
      -  Mathematical operators and functions.
      -  Covariates
      -  ``idosevar``, ``infdosevar``, ``infratevar`` variables

   -  **Cannot Include:** Structural parameters (parameters defined with
      ``stparm``), random effects, or variables defined by top-level
      assignment. Secondary parameters are functions of *fixed* effects,
      and other derived quantities, *not* the individual-specific
      parameter values or dynamic variables.

-  **Calculation:** Calculated once after all model fitting is completed.
-  **Multiple** ``secondary`` **statements:** can be included.

.. note::
   There is generally no direct equivalent to ``secondary`` parameters in standard NONMEM code.
   The ``secondary`` statement in PML is a convenience for post-processing and reporting,
   **not** for defining relationships within the core model. Do not translate simple assignments from NONMEM's ``$PK`` or ``$DES`` blocks
   into ``secondary`` statements.

**Example:**

.. code:: pml

   stparm(Cl = tvCl * exp(nCl))
   stparm(V  = tvV * exp(nV))
   fixef(tvCl = c(,5,))
   fixef(tvV = c(,50,))

   secondary(
     Halflife = log(2) / (tvCl / tvV)  // Calculate half-life from fixed effects
   )

**Keywords:** secondary parameter, derived parameter, calculated parameter, secondary, fixed effects

**See also:** Parameters, ``stparm`` Statement, Fixed Effects, Calculated Values


Data Mapping (Column Definitions)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Data mapping links columns in your input dataset to
variables and contexts within your PML model. This is done *outside* the
PML code, using a column definition file or interface.

-  **Purpose:** To tell the execution engine how to interpret the data
   in your input file.

-  **Column Definition File:** A text file (or equivalent interface)
   with mapping statements.

-  **Key Mapping Statements:**

   -  ``id(columnName)``: Maps a column to the subject ID. Example: ``id(SubjectID)``.
   -  ``time(columnName)``: Maps a column to the time variable (``t``). Example: ``time(Time)``.
   -  ``obs(observedVariable <- columnName)``: Maps a column to an observed variable. Example: ``obs(CObs <- Conc)``.
   -  ``amt(columnName)``: Maps a column to the dose amount (with ``dosepoint``). Example: ``amt(DoseAmt)``.

      -  Can map a single column containing **both** bolus and infusion amounts.

   -  ``rate(columnName)``: Maps a column to the infusion rate (with ``dosepoint``). Example: ``rate(InfRate)``.
   -  ``covr(covariateName <- columnName)``: Maps a column to a covariate (``covariate`` or ``fcovariate``). Example:
      ``covr(Weight <- BW)``.

      -  **Categorical Covariates:**

         -  With labels: ``covr(Sex <- SexColumn("Male" = 0, "Female" = 1))``
         -  Without labels: ``covr(Sex <- SexColumn())`` (First unique value is the reference category).

   -  ``fcovr(covariateName <- columnName)``: Same as ``covr``, but for ``fcovariate``.
   -  ``censor(columnName)``: Maps a column to the BQL flag from ``observe``. Example: ``censor(CObsBQL)``.
   -  ``loq(columnName)``: Maps a column to provide lower limits of quantification. Example: ``loq(LLOQ)``.
   -  ``mvd(columnName)``: Maps a column to indicate missing data values for observations. Example: ``mvd(MDV)``.
   -  ``evid(columnName)``: Maps a column to an event identifier. Example: ``evid(EVID)``.
   -  ``addl(columnName, doseCycleDescription)``: Maps a column to indicate additional doses. Example: ``addl(ADDL, 24 dt 10 bolus(A1))``.
   -  ``ii(columnName)``: Maps a column to the interdose interval. Often *derived* from ``addl``.
   -  ``dose(doseVariable <- columnName, cmt = compartmentNumber)``: *Conditional* mapping of doses. Maps ``columnName`` to
      ``doseVariable`` *only when* ``cmt`` matches ``compartmentNumber``. Essential for multiple dosepoints. Example: ``dose(AaDose <- AMT, cmt = 1)``.
   -  ``cmt(columnName)``: Maps a column specifying the compartment number (with conditional ``dose``). Example: ``cmt(CMT)``.
   -  ``ss(ssColumnName, doseCycleDescription)``: Maps a column that indicates steady-state dosing.
   -  ``reset(resetColumnName=c(lowValue, highValue))``: Maps a column to reset time and compartments
   -  ``date(dateColumnName[, formatString [, centuryBase]])``: maps date column
   -  ``dvid(columnName)``: Maps a column to an observation type identifier (multiple observation types in same data column).
      Example: ``dvid(TYPE)``. Used with conditional observation mapping.
   -  ``table(...)``: (Not for input, defines output tables).

-  **Conditional Mapping:** Use conditional logic in mappings to handle
   rows differently (e.g., based on ``CMT``, ``DVID``). Map the same
   data column to different variables, depending on context.

**Example (Conceptual Column Mappings - PK/PD, Multiple Doses, BQL):**

::

   id(ID)
   time(TIME)
   amt(AMT)
   addl(ADDL)        // Additional doses
   ii(II)            // Interdose interval
   mvd(MDV)
   evid(EVID)
   obs(CObs <- DV)    // PK observations
   obs(EObs <- DV)  // PD observations
   covr(Weight <- WEIGHT)
   covr(Sex <- SEX("Male" = 0, "Female" = 1))
   censor(CObsBQL)  // BQL flag for PK observations
   loq(LOQ)
   dose(AaDose <- AMT, cmt = 1)   // Map AMT to AaDose when CMT=1 (bolus)
   dose(AaInfDose <- AMT, cmt = 1) // Map AMT to AaInfDose when CMT=1 (infusion)
   rate(AaInfRate <- RATE)     // Infusion rate
   dvid(TYPE) // DVID for distinguishing PK/PD observations

**Keywords:** data mapping, column mapping, input data, dataset, id,
time, obs, amt, evid, rate, covariate, censor, loq, dvid, dose, addl,
ii, table, ss, reset, date

**See also:** Input Data, ``observe`` Statement, ``dosepoint``
Statement, Covariates, BQL Handling, Conditional Mapping


sequence Block
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``sequence`` block allows for *sequential* execution of
statements, unlike the generally declarative nature of PML. Used for
initialization, time-dependent actions, and discontinuous events.

-  **Purpose:** Define statements executed in order, at specific times.
-  **Syntax:** ``sequence { statements }``
-  **Key Feature: Sequential Execution:** Order of statements *matters*
   within a ``sequence`` block.
-  **Statements Allowed Within sequence:**

   -  Assignment statements (for variables modifiable when the model is
      stopped – integrator variables, ``real``/``double`` variables).
   -  ``if (test-expression) statement-or-block [else statement-or-block]``
      (Conditional execution). Use ternary operator (``? :``) *within*
      expressions, *not* ``if/else``.
   -  ``while (test-expression) statement-or-block`` (Looping)
   -  ``sleep(duration-expression)`` (Pauses execution)
   -  Function calls

-  **Execution Timing:**

   -  ``sequence`` blocks start *before* model simulation (at time 0).
   -  Continue until ``sleep`` or end of block.
   -  ``sleep`` pauses, resuming at the future time.

-  **Multiple** ``sequence`` **statements** can be in a model, and they are executed as if in parallel.
-  **Reset:** ``sequence`` statement(s) are restarted when a reset is encountered in the data
-  **Restrictions:**

   -  It is not strongly not recommended to modify inside ``sequence``
      fixed effects, random effects, residual erros, structural
      parameters. It is impossible to modify observable variables.
      **Example (Initializing Compartments):**

.. code:: pml

   sequence {
     A1 = 100  // Initialize A1 to 100 at time 0
     A2 = 0    // Initialize A2 to 0 at time 0
   }

**Example (Time-Dependent Action):**

.. code:: pml

   sequence {
     sleep(5)        // Wait 5 time units
     DoseRate = 0   // Turn off an infusion
   }

**Example (Loop and Conditional):**

.. code:: pml

   real(i)
   sequence {
     i = 0
     while (i < 10) {
       if (Concentration < Threshold) {
         DoseRate = HighRate
       } else {
         DoseRate = LowRate
       }
       sleep(1)
       i = i + 1
     }
   }

**Keywords:** sequence, action code, sequential execution, sleep, if,
else, while, initialization, time-dependent actions

**See also:** Statements, Blocks, ``sleep`` Function, ``if`` and Ternary Operator, Time-Based Models, Action Code, ``real`` Statement


real and double
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``real`` and ``double`` are synonyms, declaring variables
as double-precision floating-point numbers *modifiable* within
``sequence`` blocks.

-  **Purpose:** Declare variables to be modified in ``sequence`` blocks.
-  **Syntax:** ``real(variableName1, variableName2, ...)`` or ``double(variableName1, variableName2, ...)``
-  **Double Precision:** ``real``/``double`` variables are double-precision.
-  **Modifiable in sequence:** Can be assigned new values *within* ``sequence`` blocks (unlike top-level assignments).

**Example:**

.. code:: pml

   real(Counter, Flag)  // Declare Counter and Flag

   sequence {
     Counter = 0
     while (Counter < 10) {
       Counter = Counter + 1
       sleep(1)
     }
     Flag = if (Concentration > Threshold) 1 else 0 //use ternary operator
   }

**Keywords:** real, double, variable declaration, sequence, modifiable variable

**See also:** Variables, ``sequence`` Block, Assignment Statements


Model Generation Guidelines
------------------------------------------------------------------------

Model Generation Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This checklist provides best practices and common pitfalls
for generating correct PML models. It covers statement ordering,
parameter definition, error models, covariate incorporation, and
built-in functions, helping to avoid mistakes and improve
identifiability.

1. **Statement Ordering (Recommended Order):**

   -  **Covariate Declarations:** ``covariate``, ``fcovariate``, ``interpolate``.
   -  ``dosepoint`` and ``delayInfCpt``: Define dosing. *Before* ``deriv`` referencing the dosed compartment.
   -  **Concentration Calculation:** E.g., ``C = A1 / V``. *Before* ``deriv`` using ``C``.
   -  ``deriv``: Define differential equations.
   -  ``error``: Define error variables (and their *numeric* standard deviations).
   -  ``observe``: Link predictions to observations, specify error model.
   -  ``stparm``: Define structural parameters. *After* covariate declarations, ``dosepoint``, and calculations they depend on.
   -  ``fixef``: Define fixed effects (population parameters).
   -  ``ranef``: Define random effects (inter-individual variability).
   -  ``secondary``: Define secondary (derived) parameters.
   -  ``sequence``: For initialization (beginning) or time-dependent actions.

2. **Structural Parameter Definition (stparm):**

   -  **Common Styles:**

      -  ``Product * exp(eta)``: ``parameter = tvParameter * exp(nParameter)`` (Log-normal - for positive-only parameters like V, Cl, Ka).
      -  ``Sum * exp(eta)``: ``parameter = (tvParameter + covariate_effects) * exp(nParameter)``.
      -  ``exp(Sum + eta)``: ``parameter = exp(tvParameter + covariate_effects + nParameter)``.
      -  ``ilogit(Sum + eta)``: ``parameter = ilogit(tvParameter + covariate_effects + nParameter)``
         (For parameters between 0 and 1, like bioavailability).
      -  ``Sum + eta``: ``parameter = tvParameter + covariate_effects + nParameter``
         (Normal - for parameters that can be positive or negative, like E0, Emax).

   -  **Choosing the Right Style:**

      -  **Positive-Only (V, Cl, Ka, etc.):** ``Product * exp(eta)`` is generally preferred.
      -  **Positive or Negative (E0, Emax, etc.):** ``Sum + eta`` is appropriate.
      -  **Between 0 and 1 (Bioavailability):** ``ilogit(Sum + eta)`` is ideal.

   -  ``stparm`` **Restrictions:** Within ``stparm``, *only* use:

      -  Fixed effects (typically ``tv`` prefix).
      -  Random effects (typically ``n`` prefix).
      -  Declared covariates.
      -  Mathematical operators and functions.
      -  *Cannot* use variables defined by assignment (e.g.,
         ``C = A1 / V``).

3. **Covariate Incorporation:**

   -  **Declaration:** Covariates *must* be declared (``covariate``,
      ``fcovariate``, or ``interpolate``).

   -  **Centering (Continuous Covariates):** Improves stability and
      reduces correlation.

      -  **Syntax:** ``(CovariateName / CenterValue)`` (multiplicative)
         or ``(CovariateName - CenterValue)`` (additive).
      -  **Center Value:** Mean, median, or clinically relevant value.

   -  **Categorical Covariates:** Use
      ``(CovariateName == CategoryValue)`` in ``stparm``. The first
      category is the reference. *Mapping is done in the column
      definition file.*

   -  **Examples (stparm Styles with Covariates):**

      .. code:: pml

         # Product * exp(eta) (most common for positive parameters)
         stparm(V = tvV * (Weight / 70)^dVdWt * exp(nV))  # Allometric scaling
         stparm(Cl = tvCl * exp(dCldSex * (Sex == 1)) * exp(nCl)) # Sex effect

         # Sum * exp(eta)
         stparm(V = (tvV + dVdWt * (Weight - 70)) * exp(nV))

         # exp(Sum + eta)
         stparm(V = exp(tvV + dVdWt * (Weight - 70) + nV))

         # ilogit(Sum + eta) (for parameters between 0 and 1)
         stparm(F = ilogit(tvF + dFdWt * (Weight - 70) + nF))

         # Sum + eta (for parameters that can be positive or negative)
         stparm(E0 = tvE0 + dE0dWt * (Weight - 70) + nE0)

         fcovariate(Weight)
         fcovariate(Sex()) #categorical covariate

4. **Error Model Specification:**

   -  ``error``: Define error variables and their *numeric* standard deviations.
   -  ``observe``: Link predictions to observations, specify error model (additive, proportional, combined, power,
      log-additive). Includes *one* error variable.
   -  ``LL``: For custom likelihoods.
   -  Use prescribed error variable names (like ``CEps``)
   -  Select an error model appropriate for your data.
   -  "**Standard Deviation vs. Variance:** Ensure the value provided in
      the ``error`` statement is the *standard deviation*, not the
      variance. If translating from NONMEM, remember to take the square
      root of the ``$SIGMA`` value (if it represents variance)."

5. **Initialization:**

   -  ``deriv`` compartments are initialized to 0. ``sequence``
      overrides this.
   -  Only ``real``/``double``, integrator, and ``urinecpt`` variables
      are modifiable in ``sequence``.
   -  Do not include explicit compartment initializations within
      sequence blocks unless specifically required

6. **Use of Built-In Functions:**

   -  Use functions for clarity and efficiency (e.g., ``exp``, ``log``,
      ``sqrt``, ``ilogit``, ``phi``, ``lnorm``).

7. **Review and Validation:**

   -  **Syntax Check:** Double-check syntax.
   -  **Simulation Testing:** Validate by simulating scenarios.
   -  **Parameter Estimates and SEs:** Check for reasonableness. Large
      values or high correlations can indicate problems.
   -  **Documentation:** Include comments.

8. **Identifiability:**

   -  Be aware of *identifiability*. Can parameters be uniquely
      estimated? Overparameterization can lead to non-identifiability.

**Example (Guideline Summary):**

.. code:: pml

   test() {
     fcovariate(Weight)  # Declare covariate early
     fcovariate(Sex())    # Declare categorical covariate

     dosepoint(Aa, tlag = Tlag)  # Dosepoint (with structural lag time)
     C = A1 / V                # Define concentration *before* using it

     deriv(Aa = -Ka * Aa)      # Absorption compartment
     deriv(A1 = Ka * Aa - Cl * C - Cl2 * (C - C2) - Cl3 * (C - C3))  # Central
     deriv(A2 = Cl2 * (C - C2))                                    # Peripheral 2
     deriv(A3 = Cl3 * (C - C3))                                    # Peripheral 3
     C2 = A2/V2
     C3 = A3/V3

     error(CEps = 0.02)       # Numeric SD value!
     observe(CObs = C * (1 + CEps))  # Proportional error

     # Structural parameters (log-normal, with covariate effects)
     stparm(
       Ka   = tvKa * exp(nKa),
       V    = tvV * (Weight / 70)^dVdWt * exp(nV),         # Allometric scaling
       Cl   = tvCl * exp(dCldSex * (Sex == 1)) * exp(nCl),  # Sex effect
       Cl2  = tvCl2 * exp(nCl2),
       V2   = tvV2 * exp(nV2),
       Cl3  = tvCl3 * exp(nCl3),
       V3   = tvV3 * exp(nV3),
       Tlag = tvTlag * exp(nTlag)
     )

     # Fixed effects
     fixef(
       tvKa   = c(, 1, ),
       tvV    = c(, 50, ),
       tvCl   = c(, 5, ),
       tvCl2  = c(, 2, ),
       tvV2   = c(, 30, ),
       tvCl3  = c(, 1, ),
       tvV3   = c(, 20, ),
       tvTlag = c(, 0.5, ),
       dVdWt  = c(, 0.75, ),  # Fixed effect for Weight on V
       dCldSex = c(, 0, )     # Fixed effect for Sex on Cl
     )

     # Random effects
       ranef(diag(nV, nCl, nCl2, nV2, nCl3, nV3, nKa, nTlag) =
         c(0.09, 0.04, 0.04, 0.09, 0.04, 0.09, 0.04, 0.01)
     )
   }

**Keywords:** best practices, checklist, troubleshooting, model generation, PML, common pitfalls, validation, syntax, ordering,
parameterization, structural parameters, covariates, centering, error models

**See also:**

-  Basic Model Structure and Statements
-  Parameter Declarations
-  Covariates
-  Structural Model Definition
-  Observation and Error Models
-  Delays
-  Built-In Functions
-  Data Mapping


Modeling Complex Absorption Schemes
------------------------------------------------------------------------

Demonstrates how to combine multiple ``dosepoint``
statements and their options (``bioavail``, ``tlag``, ``duration``) to
model formulations with complex absorption kinetics, such as
simultaneous or sequential processes.

The ``dosepoint`` statement is highly flexible. By using multiple
``dosepoint`` statements, you can model complex drug delivery systems
where a single dose (``AMT`` from the data) is split into different
pathways or scheduled to occur sequentially.

.. _a-simultaneous-parallel-absorption-zero-order-and-first-order:

A. Simultaneous (Parallel) Absorption (Zero-Order and First-Order)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This pattern models a formulation with both immediate and sustained
release components that begin absorbing at the same time. A single dose
is split between a first-order and a zero-order process using a
fractional bioavailability parameter (``Fr``).

-  **Key Concept:** Two ``dosepoint`` statements are used. One
   (``dosepoint(Aa, bioavail = Fr)``) directs a fraction of the dose to
   a first-order process. The other
   (``dosepoint(A1, bioavail = 1 - Fr, duration = Dur)``) directs the
   remaining fraction to a zero-order process.

**Example Code (Simultaneous ZO/FO):**

.. code:: pml

   test() {
       # PARALLEL PATHWAYS:
       # 1. First-order absorption for fraction 'Fr'.
       dosepoint(Aa, bioavail = Fr)
       # 2. Zero-order absorption for fraction '(1 - Fr)' over duration 'Dur'.
       dosepoint(A1, bioavail = 1 - Fr, duration = Dur)

       # Model structure
       C = A1 / V
       deriv(Aa = -Ka * Aa)
       deriv(A1 = Ka * Aa - Cl * C)

       # ... observe/error statements ...

       # Structural parameters
       stparm(Fr = ilogit(tvFr_logit + nFr_logit)) // Fraction for 1st-order
       stparm(Dur = tvDur * exp(nDur)) // Duration for 0-order
       # ... stparm for Cl, V, Ka ...

       # ... fixef/ranef statements ...
   }

.. _b-sequential-absorption-zero-order-followed-by-first-order---zofo:

B. Sequential Absorption (Zero-Order followed by First-Order - ZOFO)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This pattern models a formulation where an initial zero-order absorption
phase is immediately followed by a first-order absorption phase.

-  **Key Concept:** The sequence is created by using the same parameter
   (``D`` in this example) to define the ``duration`` of the zero-order
   process and the ``tlag`` (time lag) of the first-order process. This
   elegantly ensures the second process begins precisely when the first
   one ends. This method is compatible with closed-form (``cfMicro``)
   solutions.

**Example Code (Sequential ZOFO):**

.. code:: pml

   test() {
       # This model uses cfMicro because the time-dependency is handled by
       # the event scheduler (dosepoint), not by changing the ODEs themselves.
       cfMicro(A1, Cl / V, first = (Aa = Ka))
       C = A1 / V

       # SEQUENTIAL PATHWAYS:
       # 1. First-Order Pathway:
       # A fraction 'Fr' of the dose is sent to the absorption depot 'Aa',
       # but its absorption is DELAYED by 'D' time units.
       dosepoint(Aa, tlag = D, bioavail = Fr)

       # 2. Zero-Order Pathway:
       # The remaining fraction '(1-Fr)' is absorbed into the central
       # compartment 'A1' over a DURATION of 'D' time units, starting at time 0.
       dosepoint(A1, bioavail = 1 - Fr, duration = D)

       # Define the fraction 'Fr' to be absorbed first-order (after the lag)
       stparm(Fr = ilogit(tvFr_logit + nFr_logit))
       fixef(tvFr_logit = c(, 0, ))
       ranef(diag(nFr_logit) = c(0.09))

       # Define the duration/tlag parameter 'D'
       stparm(D = tvD * exp(nD))
       fixef(tvD = c(, 1, ))
       ranef(diag(nD) = c(0.09))

       # ... observe/error statements ...
       # ... stparm, fixef, ranef for Cl, V, Ka ...
   }

.. _c-splitting-a-single-dose-into-different-administration-profiles-eg-bolus--infusion:

C. Splitting a Single Dose into Different Administration Profiles (e.g., Bolus + Infusion)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This pattern is used for a single dose amount that is administered in
two different ways simultaneously (e.g., a formulation that gives an
initial bolus effect while also starting a slow-release infusion).

-  **Key Concept:** This is achieved by using ``dosepoint`` and
   ``dosepoint2`` on the *same compartment*. The crucial ``split``
   argument is added to the first ``dosepoint`` statement. This allows a
   single dose amount from one column in the data (e.g., ``AMT``) to be
   divided between the two statements using their respective
   ``bioavail`` options.

**Example (50% Bolus, 50% Infusion over 3 time units):**

This model takes a single dose amount and administers 50% of it as an
instantaneous bolus into ``Aa``, while simultaneously starting a 3-hour
infusion of the other 50% into the same ``Aa`` compartment.

**PML Code:**

.. code:: pml

   test(){
       # Define the central compartment and concentration
       deriv(A1 = - (Cl * C) + (Aa * Ka))
       deriv(Aa = - (Aa * Ka))
       C = A1 / V

       # DOSE SPLITTING:
       # 1. Define the bolus part. 'bioavail=(.5)' takes 50% of the dose.
       #    'split' is ESSENTIAL to allow the same data column to be used for dosepoint2.
       dosepoint(Aa, bioavail = (.5), split)

       # 2. Define the infusion part on the same compartment 'Aa'.
       #    'bioavail=(.5)' takes the other 50% of the dose.
       #    'duration=(3)' defines the zero-order infusion time.
       dosepoint2(Aa, bioavail = (.5), duration = (3))

       # ... observe/error and parameter definition statements ...
       error(CEps = 30)
       observe(CObs = C + CEps)
       stparm(V = tvV * exp(nV))
       stparm(Cl = tvCl * exp(nCl))
       stparm(Ka = tvKa * exp(nKa))
       # ... fixef/ranef statements ...
   }

**Corresponding Column Definition Mapping:**

::

   # Because 'split' is used, both dose() and dose2() can map to "AMT".
   dose(Aa<-"AMT")
   dose2(Aa<-"AMT")

.. _d-parallel-absorption-with-independent-lag-times:

D. Parallel Absorption with Independent Lag Times
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For maximum flexibility, especially with complex formulations, you can
assign independent lag times to each parallel absorption pathway. This
allows for modeling scenarios where two different release mechanisms
from a single dose not only have different profiles (e.g., zero-order
vs. first-order) but also start at different times.

-  **Key Concept:** Use a separate ``tlag`` argument in each
   ``dosepoint`` statement. Each ``tlag`` can be linked to a different
   structural parameter, allowing them to be estimated independently.

**Example (Simultaneous ZOFO with Independent Lags):** This model splits
a dose into a first-order pathway and a zero-order pathway, where each
can start after its own unique delay.

**PML Code Snippet (Focus on dosepoint):**

.. code:: pml

       # 1. First-Order Pathway with its own lag time 'Tlag_FO'
       dosepoint(Aa, bioavail = Fr_FO, tlag = Tlag_FO)

       # 2. Zero-Order Pathway with its own lag time 'Tlag_ZO'
       dosepoint(A1, bioavail = 1 - Fr_FO, duration = Dur_ZO, tlag = Tlag_ZO)

       # ... parameter definitions for Tlag_FO and Tlag_ZO would be separate ...
       stparm(Tlag_FO = tvTlag_FO * exp(nTlag_FO))
       stparm(Tlag_ZO = tvTlag_ZO * exp(nTlag_ZO))

**Keywords:** absorption, parallel absorption, sequential absorption,
dose splitting, dual absorption, ZOFO, lag time, tlag, duration, bioavail

**See also:** ``dosepoint`` Statement, ``split``, ``bioavail``, ``duration``, ``tlag``


Modeling Multiple Elimination Pathways
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Describes how to model drugs that are cleared by multiple
simultaneous mechanisms (e.g., a mix of linear and saturable pathways)
by summing their individual rate equations within the ``deriv``
statement.

Pharmacokinetic models in PML are modular. If a drug is eliminated by
more than one process, the total rate of elimination is simply the sum
of the rates of each individual pathway. This is implemented by
subtracting each elimination rate term within the ``deriv`` statement
for the central compartment.

**Total Elimination Rate = (Rate of Pathway 1) + (Rate of Pathway 2) +
...**

**Example: Mixed Linear and Saturable (Hill-Type) Elimination**

A common scenario is a drug cleared by both a first-order (linear)
process and a capacity-limited (saturable) process.

-  **Linear Pathway Rate:** ``Cl * C``
-  **Saturable Pathway Rate (with Hill):**
   ``(Vmax * C^h) / (Km^h + C^h)``

**Implementation in** ``deriv`` **Statement:** The ``deriv`` statement for
the central compartment (``A1``) would include the drug input minus both
elimination terms.

.. code:: pml

   deriv(
       A1 = (INPUT) - (Cl * C) - (Vmax * C^h) / (Km^h + C^h)
   )

**Full Example Model (from previous interaction):** This code shows the
principle in a complex model that combines parallel absorption with
mixed-order elimination. Note the two separate subtraction terms in the
``deriv(A1 = ...)`` line.

.. code:: pml

   test() {
       # Parallel absorption with independent lag times
       dosepoint(Aa, bioavail = Fr_FO, tlag = Tlag_FO)
       dosepoint(A1, bioavail = 1 - Fr_FO, duration = Dur_ZO, tlag = Tlag_ZO)

       C = A1 / V
       deriv(Aa = -Ka * Aa)
       deriv(
           # The two elimination pathways are summed here by subtracting each term
           A1 = (Ka * Aa) - ( (Cl * C) + (Vmax * C^h) / (Km^h + C^h) )
       )

       # ... observe/error statements ...

       # Structural parameters including Cl, Vmax, Km, and h
       stparm(Cl   = tvCl   * exp(nCl))       // Linear clearance
       stparm(Vmax = tvVmax * exp(nVmax))     // Saturable Vmax
       stparm(Km   = tvKm   * exp(nKm))       // Saturable Km
       stparm(h    = tvh    * exp(nh))        // Hill coefficient
       # ... other stparm, fixef, ranef statements ...
   }

**Keywords:** elimination, clearance, Michaelis-Menten, mixed-order, parallel pathways, deriv, Vmax, Km, Hill

**See also:** ``deriv`` Statement, Compartment Models, Michaelis-Menten Kinetics


Introduction to Metamodels
------------------------------------------------------------------------

The Metamodel Concept
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A metamodel, distinguished by the ``.mmdl`` file extension,
is a self-contained text file that encapsulates all necessary components
for running a Pharmacometric Modeling Language (PML) model. It serves as
a comprehensive container, bundling the model code, data file reference,
column mappings, and engine instructions into a single, human-readable
file, analogous to a NONMEM control file.

The primary purpose of a metamodel is to simplify the
execution and management of PML models, particularly within the
Certara.RsNLME ecosystem. While PML is the core modeling language for
both Phoenix NLME and RsNLME, a basic PML model file (``.mdl``) only
contains the model's structural equations and statements. It does not
specify which dataset to use, how to map data columns to model variables
(e.g., concentration, time), or what estimation engine settings to
apply.

A metamodel solves this by integrating these separate pieces of
information into a single, structured ``.mmdl`` file. This makes models
more portable, reproducible, and easier to run from both R (using
``Certara.RsNLME``) and command-line interfaces.

**Comparison with Other Systems:**

-  **Phoenix NLME Project:** In the Phoenix NLME graphical user
   interface, the project file (``.phxproj``) holds the model, data, and
   mappings together in a binary format. A metamodel provides a
   text-based, human-readable equivalent of this integration.
-  **NONMEM Control Stream:** The structure and function of a metamodel
   are conceptually very similar to a NONMEM control stream (``.ctl``
   file), which also combines model specification (``$PK``, ``$ERROR``),
   data linkage (``$DATA``), and estimation instructions (``$EST``) into
   one file.

**Metamodel Structure:** Metamodels are organized into distinct blocks,
each beginning with a double number sign (``##``) followed by the
block's name (e.g., ``##DATA``, ``##MODEL``). Comments within a
metamodel follow standard PML syntax: ``#`` or ``//`` for single-line
comments, and ``/* ... */`` for multi-line comments.

**Keywords:** metamodel, .mmdl, container, PML, RsNLME, Phoenix NLME, NONMEM control file

**See also:** Metamodel Blocks, PML Model Structure


Metamodel Structure
------------------------------------------------------------------------

Metamodel Blocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A metamodel file is structured into distinct,
case-insensitive blocks, each starting with a double number sign
(``##``) followed by the block name. The most critical blocks are
``##DATA``, ``##MODEL``, and ``##MAP``, which define the dataset, the
PML code, and the column mappings, respectively. Other blocks like
``##ESTARGS`` and ``##TABLES`` provide instructions for model execution
and output generation.

The following blocks are used to organize the information
within a ``.mmdl`` file.

-  **Informational Blocks:**

   -  ``##Author``: Specifies the name of the model author (e.g., ``##Author: A. User``).
   -  ``##Description``: Provides a text description of the model's purpose. This is used by external tools like Pirana for display.
   -  ``##Based on``: Indicates the filename of a parent or reference metamodel, used by Pirana to construct model development trees.
   -  These three blocks are optional and are not used by the NLME engine during estimation.

-  ``##DATA``

   -  **Required.** This block specifies the path to the input dataset
      **on a single line**.
   -  The path can be absolute or relative to the location of the
      ``.mmdl`` file.
   -  The ``Certara.RsNLME`` package uses the ``data.table::fread()``
      function to load the specified data file.
   -  **Syntax:** ``##DATA path/to/your/data.csv``

-  ``##MODEL``

   -  **Required.** This block contains the complete Pharmacometric
      Modeling Language (PML) code for the model.
   -  The syntax within this block must conform to standard PML rules.
   -  **Syntax:**
      ::

         ##MODEL
         test() {
           // PML statements go here
         }

-  ``##MAP``

   -  Defines the mappings between PML model variables and the columns
      in the dataset specified in ``##DATA``.
   -  **Syntax:** Mappings are defined using
      ``variableName = columnName``.
   -  If a mapping for a model variable is omitted, the engine assumes
      the data column has the exact same name as the model variable
      (e.g., a mapping for ``CObs`` is equivalent to writing
      ``CObs = CObs``).
   -  This block is also used to map **special variables** that control
      model behavior but may not be explicitly defined in the
      ``##MODEL`` block:

      -  ``id``: **Required for population models.** Maps up to five
         columns that uniquely identify each subject. If unmapped, the
         model is treated as an individual fit. (e.g.,
         ``id = SubjectID``).
      -  ``time``: **Required for time-based models** (any model
         with a ``deriv`` statement). Maps the time column. (e.g.,
         ``time = Time``).
      -  ``dosingCompartmentName_Rate`` / ``..._Duration``:
         Specifies that a dosing compartment receives an infusion, with
         the rate or duration defined in the mapped data column. (e.g.,
         ``A1_Duration = DUR``).
      -  ``SS``, ``ADDL``, ``II``: Map columns containing
         steady-state flags, additional dose flags, and the inter-dose
         interval, respectively. ``II`` is required if ``SS`` or
         ``ADDL`` are used.
      -  ``MDV``: Maps a column containing Missing Data Value flags.
         Rows with a non-zero value in this column are ignored during
         estimation.
      -  ``Reset``: Maps a column that flags when to reset the
         model's state (time and compartment amounts).

   -  **Categorical Covariates:** Allows for on-the-fly definition of
      labels for character-based categorical data. (e.g.,
      ``Sex = Gender(Male = 0, Female = 1)``).

-  ``##COLDEF``

   -  Provides an alternative and more powerful way to define column
      mappings using the full native syntax of the NLME engine's column
      definition file.
   -  This block is useful for complex mappings that cannot be expressed
      through the simpler ``##MAP`` syntax.
   -  Definitions from ``##MAP`` and ``##COLDEF`` are combined. If there
      is a conflict, the ``##COLDEF`` definition may take precedence.
   -  **Example Syntax:**
      ::

         ##COLDEF
         id("id")
         obs(CObs<-"conc")
         covr(sex<-"sex"("male" = 0, "female" = 1))

-  ``##DOSING CYCLE``

   -  An alternative block specifically for defining ``ADDL`` or ``SS``
      dosing cycles without needing to add ``ADDL`` or ``II`` columns to
      the source dataset.
   -  **Syntax Example:**
      ``SS = flag_col Dosepoint = A1 Amount = 100 Delta = 24``

-  ``##ESTARGS``

   -  Specifies arguments for the estimation engine, using the syntax of
      the ``engineParams()`` function in the ``Certara.RsNLME`` package.
      Multiple arguments can be separated by commas or newlines.
   -  If this block is omitted, default engine parameters are used.
   -  **Sequential Estimation:** Multiple ``##ESTARGS`` blocks can be
      included. They will be executed sequentially, with each run
      starting from the final parameter estimates of the previous one.
   -  **Example Syntax:**
      ``##ESTARGS method = QRPEM, numIterations = 50``

-  ``##SIMARGS``

   -  Specifies arguments for model simulation runs. Key arguments
      include ``numReplicates`` and ``seed``.
   -  Multiple ``##SIMARGS`` and ``##ESTARGS`` blocks can be used. All
      estimation runs (``##ESTARGS``) are completed before any
      simulation runs (``##SIMARGS``) begin.
   -  **Example Syntax:** ``##SIMARGS numReplicates = 200, seed = 1234``

-  ``##TABLES``

   -  Defines one or more custom output tables. By default, the engine
      already creates a ``posthoc.csv`` table.
   -  Uses the standard PML ``table()`` syntax. Tables can also be
      defined in the ``##COLDEF`` block.
   -  **Example Syntax:**
      ``##TABLES table(file="conc_vs_time.csv", time(seq(0, 24, 0.5)), C, V)``

**Keywords:** ##Author, ##Description, ##Based on, ##DATA, ##MAP,
##COLDEF, ##MODEL, ##ESTARGS, ##SIMARGS, ##TABLES, ##DOSING CYCLE,
block, metamodel structure

**See also:** The Metamodel Concept, PML Model Structure.


Execution Control and Output
------------------------------------------------------------------------

##ESTARGS: Estimation Engine Arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``##ESTARGS`` block specifies arguments that control
the model estimation process, overriding the default behavior of the
NLME engine. Multiple ``##ESTARGS`` blocks can be used to define a
sequence of estimation steps. Key arguments include ``method`` to select
the algorithm and ``numIterations`` to control its duration.

The ``##ESTARGS`` block provides direct control over the
NLME estimation engine. Its arguments mirror those found in the
``engineParams()`` function of the ``Certara.RsNLME`` R package.
Arguments can be separated by commas or newlines.

**Common Use Case: Sequential Estimation** A powerful feature is the
ability to define multiple ``##ESTARGS`` blocks. They are executed in
the order they appear in the metamodel. A common strategy is to use a
fast but less precise method first to get good initial estimates, and
then use a more robust algorithm for the final estimation.

**Example of a two-stage estimation:**

::

   ##ESTARGS method = QRPEM, numIterations = 300
   ##ESTARGS method = FOCE-ELS, numIterations = 700

In this example, the engine first runs 300 iterations of the QRPEM
algorithm. The resulting parameter estimates are then used as the
starting point for a second run of 700 iterations using the FOCE-ELS
algorithm.

**Key Arguments:**

-  ``method``: Specifies the estimation algorithm. The choice of
   method is critical and depends on the model type.

   -  **For population models**, common options include:

      -  ``"QRPEM"``: A robust stochastic algorithm, good for complex
         models and finding initial estimates.
      -  ``"FOCE-ELS"``: A fast and widely used First-Order Conditional
         Estimation method. This is often the default.
      -  ``"Laplacian"``: The default method for models with BQL data or
         count data.
      -  ``"FOCE-LB"``: Similar to FOCE-ELS, the Lindstrom-Bates
         algorithm.
      -  ``"IT2S-EM"``: An iterative two-stage algorithm.

   -  **For individual models**: ``"Naive-Pooled"`` is the only option.

-  ``numIterations``: A non-negative integer specifying the maximum
   number of iterations for the chosen method.

-  ``stdErr``: Controls the method for calculating standard errors
   of the parameter estimates.

   -  Common options include ``"Sandwich"`` (the default for FOCE-type
      methods), ``"Hessian"``, and ``"Fisher-Score"``.
   -  Setting ``stdErr = "None"`` disables standard error calculation,
      which can speed up runs, especially during initial model
      development.

-  ``numIntegratePtsAGQ``: Specifies the number of quadrature points
   for Adaptive Gaussian Quadrature, used to improve accuracy in
   ``"FOCE-ELS"`` or ``"Laplacian"`` methods, particularly for models
   with high shrinkage. A value greater than 1 enables AGQ.

-  ``logTransform``: A logical value (``TRUE``/``FALSE``) that
   controls how models with a log-additive error structure (e.g.,
   ``C*exp(eps)``) are handled, typically by enabling or disabling a
   Log-Transform Both Sides (LTBS) approach during the fit.

-  ``sort``: A logical value. If ``FALSE``, it forces the engine to
   preserve the original sort order of the input dataset. This is
   critical for models with reset events or other sequence-dependent
   logic.

A full list of available arguments can be found in the
``Certara.RsNLME::engineParams()`` documentation.

**Keywords:** ##ESTARGS, engine arguments, method, numIterations, stdErr, QRPEM, FOCE, Laplacian

**See also:** Metamodel Blocks, ##SIMARGS, ##TABLES


##SIMARGS: Simulation Arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``##SIMARGS`` block configures simulation runs that are
executed *after* all model estimations are complete. Its key arguments,
``numReplicates`` and ``seed``, control the number of simulated datasets
to generate and ensure the reproducibility of the results.

The ``##SIMARGS`` block is used to specify arguments for
running simulations based on the final parameter estimates obtained from
the ``##ESTARGS`` blocks.

**Execution Order:** In a metamodel containing both ``##ESTARGS`` and
``##SIMARGS`` blocks, all estimation runs are performed first. The final
parameter estimates from the *last* completed ``##ESTARGS`` block are
then used as the basis for all subsequent simulation runs defined by
``##SIMARGS`` blocks.

**Key Arguments:**

-  ``numReplicates``: An integer specifying the number of simulation
   replicates to generate. For example, ``numReplicates = 200`` will
   create 200 simulated datasets, which is common for a Visual
   Predictive Check (VPC). The default value is 100.
-  ``seed``: An integer used to initialize the random number
   generator. Setting a specific seed ensures that simulation results
   are reproducible; running the same model with the same seed will
   produce the exact same simulated output. The default value is 1234.
-  **Other Arguments**: Technical arguments from the ``engineParams()``
   function can also be used here to control the simulation process,
   such as:

   -  ``sort``: A logical value (``TRUE``/``FALSE``) to control data
      sorting during simulation.
   -  ``ODE``, ``rtolODE``, ``atolODE``: Arguments to control the ODE
      solver settings for the simulation runs.

**Example:** This metamodel snippet first estimates the parameters and
then uses those final estimates to run a reproducible simulation.

::

   # First, estimate the model parameters
   ##ESTARGS method = FOCE-ELS, numIterations = 1000

   # Then, using the final estimates, run a simulation of 500 replicates
   ##SIMARGS numReplicates = 500, seed = 42

**Keywords:** ##SIMARGS, simulation, numReplicates, seed

**See also:** Metamodel Blocks, ##ESTARGS: Estimation Engine Arguments, ##TABLES: Defining Output Tables


##TABLES: Defining Output Tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``##TABLES`` block is used to define custom output
files containing model variables and calculated values from either
estimation or simulation runs. It is crucial to use the ``table()``
statement for estimation outputs and the ``simtbl()`` statement for
simulation outputs to ensure the correct data is generated at the right
stage.

While the NLME engine produces a default ``posthoc.csv``
file for estimation runs, the ``##TABLES`` block provides complete
control over the content, structure, and timing of custom data tables.

``table()`` vs. ``simtbl()``: This distinction is critical and
determines when the table is generated:

-  ``table(...)``: Defines an output table generated during an
   **estimation** run (from an ``##ESTARGS`` block). This is used for
   creating tables of predictions, residuals, individual parameters,
   etc., based on the original data.
-  ``simtbl(...)``: Defines an output table generated during a
   **simulation** run (from a ``##SIMARGS`` block). This is used for
   saving the results of simulations, such as data for a Visual
   Predictive Check (VPC).

**Default Table:** For estimation runs only, a ``posthoc.csv`` table is
created by default. It contains the structural parameters and covariates
for each subject at each time point present in the original input
dataset.

**Table Syntax Components:** Both ``table()`` and ``simtbl()`` share a
common syntax structure composed of several parts:

-  ``file="filename.csv"``: **(Required)** Specifies the name of the
   output CSV file.

-  **Triggers (When to write a row):** These arguments specify the
   events that cause a row to be written to the output file. Multiple
   triggers can be used.

   -  ``time(...)``: At specified time points. Can be a list of numbers
      or a sequence (e.g., ``time(0, 10, seq(2, 8, 0.1))``).
   -  ``dose(...)``: At each dosing event for the named compartment(s)
      (e.g., ``dose(A1)``).
   -  ``covr(...)``: Whenever a specified covariate's value changes
      (e.g., ``covr(BW)``).
   -  ``obs(...)``: At each time point corresponding to an observation
      of the named variable(s) (e.g., ``obs(CObs)``).

-  **Variables (What to write in the columns):**

   -  A comma-separated list of model variables (e.g., structural
      parameters, compartment amounts, concentrations) to include in the
      output (e.g., ``C, V, Cl, IPRED``).

-  **Special Variables (specvar)**:

   -  Used to request special, calculated variables that are derived by
      the engine during the run.
   -  **Rule:** The ``specvar()`` clause can **only** be used in a
      ``table()`` definition that also contains an ``obs()`` trigger.
      The special variables are calculated specifically at the
      observation time points.
   -  Common ``specvar`` variables include:

      -  ``TAD``: Time After Dose.
      -  ``IRES``: Individual Residuals.
      -  ``IWRES``: Individual Weighted Residuals.
      -  ``Weight``: The statistical weight of the current observation.

-  **Output Mode (mode)**:

   -  ``mode = keep``: This is a special mode that overrides other
      time-based triggers (``time``, ``dose``, etc.). It forces the
      output table to contain the exact same number of rows as the input
      dataset, writing output only at the original time points.

**Examples:**

-  **Post-hoc parameters at time zero:**

   ::

      ##TABLES
      table(file="parameters_t0.csv", time(0), Ka, V, Cl)

-  **Residuals and special variables at observation times:**

   ::

      ##TABLES
      table(file="residuals.csv", obs(CObs), IPRED, specvar(TAD, IRES, IWRES))

-  **A simulated dataset matching the original data structure:**

   ::

      ##TABLES
      simtbl(file="simulated_data.csv", CObs, mode = keep)

-  **A dense grid of simulated concentration profiles:**

   ::

      ##TABLES
      simtbl(file="simulation_profiles.csv", time(seq(0, 48, 0.5)), C, V, Cl)

**Keywords:** ##TABLES, table, simtbl, output, file, time, dose, covr, obs, specvar, mode, keep

**See also:** Metamodel Blocks, ##ESTARGS: Estimation Engine Arguments, ##SIMARGS: Simulation Arguments


Linking Data to the Model
------------------------------------------------------------------------

Data Mapping: ##MAP and ##COLDEF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Data mapping is the crucial step of linking columns in your
dataset to variables within your PML model. Metamodels provide two
blocks for this purpose: ``##MAP`` for simple, direct assignments and
``##COLDEF`` for the full, native column definition syntax. Both can be
used together to define all necessary connections.

For the NLME engine to understand your dataset, you must
tell it which column corresponds to subject IDs, which to time, which to
observations, and so on.

**The ##MAP Block**
^^^^^^^^^^^^^^^^^^^^^^^

The ``##MAP`` block is the primary and most convenient way to define
column mappings.

**Basic Syntax:** Mappings are specified as
``variableName = columnName`` and are all placed on the **same line** as
the ``##MAP`` keyword, separated by spaces or commas. If a model
variable is not explicitly mapped, the engine assumes the dataset
contains a column with the exact same name (e.g., ``CObs`` in the model
is implicitly mapped to a ``CObs`` column in the data).

::

   ##MAP C = CONC, Weight = BW, id = SubjectID

**Special Mappings:** The ``##MAP`` block is also used to define
mappings for special variables that are essential for model execution
but are not part of the PML model code itself.

-  ``id = columnName``: **(Required for population models)**. Maps a
   column to be used as the subject identifier. Up to five
   comma-separated columns can be specified for composite keys. If
   ``id`` is not mapped, the data is treated as if from a single
   individual.

-  ``time = columnName``: **(Required for time-based models)**. Maps
   the column containing the time of the records.

-  **Infusion Mappings**: To specify an infusion dose, you map a rate or
   a duration to a specific dosing compartment from your model.

   -  ``dosingCompartmentName_Rate = columnName``: Maps an infusion rate
      for the specified dosepoint.
   -  ``dosingCompartmentName_Duration = columnName``: Maps an infusion
      duration for the specified dosepoint.
   -  Example: ``A1_Duration = DUR`` maps the ``DUR`` column to the
      duration of infusions into compartment ``A1``.

-  **Dosing Event Mappings**:

   -  ``SS = columnName``: Maps the column containing the steady-state
      dose flag.
   -  ``ADDL = columnName``: Maps the column containing the "additional
      doses" flag.
   -  ``II = columnName``: **(Required if SS or ADDL are used)**. Maps the column containing the inter-dose interval.

-  **Data Flag Mappings**:

   -  ``MDV = columnName``: Maps the "Missing Data Value" column. Rows
      where this column contains a non-zero value are ignored for
      parameter estimation.
   -  ``Reset = columnName``: Maps the column containing a reset flag.
      On rows with a non-zero value, the model's state (time and
      compartment amounts) is reset.

-  **Categorical Covariate Labeling**:

   -  For a categorical covariate (defined with ``covariate(Sex())`` in
      PML), you can provide human-readable labels for the values in your
      data.
   -  **Syntax:**
      ``ModelVariableName = ColumnName(Label1 = Value1, Label2 = Value2)``
   -  **Example:** ``Sex = Gender(Male = 0, Female = 1)`` maps the
      ``Gender`` data column to the ``Sex`` model variable, treating
      rows with ``0`` as "Male" and ``1`` as "Female".

**The ##COLDEF Block**
^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``##COLDEF`` block provides a more powerful and flexible alternative
for defining column mappings. It uses the full, native syntax that the
NLME engine uses internally, which is documented in the PML reference
guides.

**When to Use** ``##COLDEF``: You should use ``##COLDEF`` when a mapping
is too complex for the simple ``##MAP`` syntax. This is rare, but can
occur with advanced model structures.

**Relationship with** ``##MAP``: You can use both ``##MAP`` and
``##COLDEF`` in the same metamodel. The engine will combine the
definitions from both blocks. If a mapping is defined in both places,
the ``##COLDEF`` definition may take precedence.

**Example using native syntax:**

::

   ##COLDEF
     id("Subject")
     time("Time")
     dose(A1<-"Dose")
     obs(CObs<-"Conc")
     covr(wt<-"Weight")

**Keywords:** ##MAP, ##COLDEF, mapping, id, time, rate, duration, SS, ADDL, II, MDV, Reset, categorical covariate

**See also:** Metamodel Blocks, ##DATA, ##DOSING CYCLE


Advanced Dosing and a Complete Example
------------------------------------------------------------------------

##DOSING CYCLE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``##DOSING CYCLE`` block provides an alternative, powerful syntax for defining steady-state (``SS``) or additional
(``ADDL``) dosing events directly within the metamodel, without requiring pre-existing ``ADDL`` or ``II`` columns in the dataset. This
is particularly useful for simulations or when the dosing schedule is fixed. It defines the parameters of a dosing regimen that is triggered
by a flag in a specified data column.

While the ``##MAP`` block can link existing ``ADDL`` and ``II`` data columns to the model, the ``##DOSING CYCLE`` block allows
you to *define* the dosing cycle itself based on a trigger column.

**Syntax:** The block begins with either ``SS`` or ``ADDL``, followed by
a series of ``key = value`` pairs.

-  **For Steady-State Dosing (SS)**:
   ``SS = [COL] Dosepoint = [CMT] Amount = [NUM/COL] Delta = [NUM/COL] Rate = [NUM/COL] Duration = [NUM/COL]``

-  **For Additional Doses (ADDL)**:
   ``ADDL = [COL] Delta = [NUM/COL] Dosepoint = [CMT] Amount = [NUM/COL] Rate = [NUM/COL] Duration = [NUM/COL]``

**Key-Value Pairs:**

-  ``SS = [COL]`` or ``ADDL = [COL]``: **(Required)** Specifies the
   data column (``[COL]``) containing the flag that triggers the dosing
   cycle. The cycle is initiated on rows where this column has a
   non-zero value.
-  ``Dosepoint = [CMT]``: **(Required)** The name of the dosing
   compartment (``[CMT]``) in the PML model that will receive the doses.
-  ``Amount = [NUM/COL]``: The dose amount. Can be a fixed number
   (``[NUM]``) or sourced from a data column (``[COL]``).
-  ``Delta = [NUM/COL]``: The inter-dose interval (equivalent to
   ``II``). Can be a fixed number or sourced from a data column.
-  ``Rate = [NUM/COL]``: The infusion rate for the doses.
-  ``Duration = [NUM/COL]``: The infusion duration for the doses.

**Example:** This example defines a steady-state dosing regimen
triggered by the ``ss_flag`` column. Each cycle consists of a 100-unit
dose administered as a 2-hour infusion into compartment ``A1`` every 24
hours.

::

   ##DOSING CYCLE
   SS = ss_flag Dosepoint = A1 Amount = 100 Duration = 2 Delta = 24

**Keywords:** ##DOSING CYCLE, SS, ADDL, steady-state, additional doses, Delta, Amount, Rate, Duration


Complete Metamodel Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section provides a complete, annotated example of a
``.mmdl`` file for a one-compartment IV infusion model, demonstrating
how all the different blocks work together.

This example brings together all the concepts into a single
``.mmdl`` file for a one-compartment IV infusion model for Warfarin.

::

   ##Description: 1-Cpt PK model with IV infusion for Warfarin
   ##Author: A. User
   ##Based on: Base_1Cpt.mmdl

   ##DATA ./warfarin_data.csv

   ##MAP id = Subject, time = Time, A1_Duration = DUR, A1 = Dose 

   ##MODEL
   test() {
     # 1-compartment model, clearance parameterization
     cfMicro(A1, Cl / V)
     C = A1 / V
     
     # Define dosepoint to receive infusions
     dosepoint(A1, idosevar = A1Dose)

     # Proportional residual error model
     error(CEps = 0.1)
     observe(CObs = C * (1 + CEps))
     
     # Structural parameters with random effects
     stparm(Cl = tvCl * exp(nCl))
     stparm(V = tvV * exp(nV))
     
     fixef(tvCl = c(, 0.1, ))
     fixef(tvV = c(, 8, ))
     
     ranef(diag(nCl, nV) = c(0.09, 0.09))
   }

   ##ESTARGS
     method = FOCE-ELS
     numIterations = 1000
     stdErr = "Sandwich"
     
   ##SIMARGS
     numReplicates = 500
     seed = 42

   ##TABLES
     # Estimation table with residuals
     table(file="residuals_output.csv", obs(CObs), specvar(IRES, IWRES))
     # Simulation table matching original data structure
     simtbl(file="simulation_output.csv", C, CObs, mode = keep)

**Keywords:** example, metamodel, .mmdl, complete

**See also:** Metamodel Blocks, ##MAP: Data Mapping, PML Model Structure


Automated Model Search with pyDarwin
------------------------------------------------------------------------

The Metamodel as a Template File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a ``pyDarwin`` search, any valid metamodel (``.mmdl``)
file can serve as a template. It becomes a template by including one or
more special placeholders, called **tokens**, which are inserted at
locations where you want to test different model variations.

The template file provides the foundational structure for
every model that will be generated during the automated search.

**Token Syntax:** The specific token syntax required is
``{TOKEN_NAME[index]}``.

**Note on Comments:** The rule to not use tokens in comments means that
the token syntax itself (e.g., ``{_COV_Cl[1]}``) should not be placed
inside a comment line. Standard comments that describe the purpose of a
tokenized section are perfectly acceptable and good practice.

-  **Correct:**

   .. code:: pml

      # Token to modify the Cl equation
      stparm(Cl = tvCl {_COV_Cl[1]} * exp(nCl))

-  **Incorrect:**

   .. code:: pml

      # The following token {_COV_Cl[1]} adds the covariate effect.
      stparm(Cl = tvCl {_COV_Cl[1]} * exp(nCl))

-  ``TOKEN_NAME``: This is the name of the token, which must
   correspond directly to a key in the accompanying ``tokens.json``
   file. Token names often start with an underscore (e.g., ``_COV``,
   ``_nCl``) to make them easily identifiable, but this is a convention,
   not a requirement.

-  ``[index]``: This is a **1-based** integer. It specifies which
   piece of text to select from a chosen option in the ``tokens.json``
   file. Since options in the ``tokens.json`` file are defined as an
   array of text strings, the index selects which string from that array
   to insert.

**Example of Token Usage:** A token in ``tokens.json`` might be defined
like this:

.. code:: json

   "_COV_Cl": [
       [ "" , "" ],
       [ " * (BW/70)^dBWdCl" , "\n\tfixef(dBWdCl = c(, 0.75, ))" ]
   ]

In the metamodel template, you would use two placeholders to insert this
effect:

.. code:: pml

      ##MODEL
     ...
     stparm(Cl = tvCl {_COV_Cl[1]} * exp(nCl))
     ...
     fixef(tvCl = c(, 1,))
     {_COV_Cl[2]}
     ...

If ``pyDarwin`` selects the second option ("on"), it will:

1. Replace ``{_COV_Cl[1]}`` with the first string: ``* (BW/70)^dBWdCl``.
2. Replace ``{_COV_Cl[2]}`` with the second string:
   ``\n\tfixef(dBWdCl = c(, 0.75, ))``.

This two-part substitution allows a single token option to modify
multiple parts of the model code simultaneously (e.g., both the
``stparm`` and ``fixef`` blocks).

**Placement of Tokens:** Tokens can be placed anywhere within the
metamodel file, including:

-  Inside the ``##MODEL`` block (most common), to change structural
   equations, parameter definitions, or error models.
-  Inside the ``##MAP`` block, to test different column mappings.
-  Inside ``##ESTARGS`` or ``##TABLES`` blocks, to test different engine
   parameters or output definitions.

**The Golden Rule:** The fundamental rule of creating a template is that
after ``pyDarwin`` performs all the token substitutions for any given
combination of choices, the resulting, fully-assembled ``.mmdl`` file
**must be a syntactically valid metamodel** that can be executed by the
NLME engine.

**Keywords:** template, token, placeholder, metamodel, pyDarwin, syntax, {TOKEN[index]}

**See also:** Introduction to pyDarwin Integration, The tokens.json File


.. _title-the-tokensjson-file-defining-the-search-space:

The tokens.json File: Defining the Search Space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``tokens.json`` file is a required companion to the
metamodel template. It is a JSON-formatted text file that defines all
the possible code snippets that can be substituted into the tokens in
the template. The structure of this file dictates the dimensions and
options of the model search.

**File Structure:** The ``tokens.json`` file has a specific structure:

-  It is a single JSON object, enclosed in curly braces ``{}``.
-  The top-level keys of this object must exactly match the
   ``TOKEN_NAME``\ s used in the metamodel template.
-  The value for each ``TOKEN_NAME`` key is an **array of options**.
-  Each **option** is itself an **array of one or more text strings**.

**Example Structure:**

.. code:: json

   {
     "TOKEN_NAME_1": [
       [ "text for option 1, index 1" , "text for option 1, index 2" ],
       [ "text for option 2, index 1" , "text for option 2, index 2" ]
     ],
     "TOKEN_NAME_2": [
       [ "text for option 1, index 1" ],
       [ "text for option 2, index 1" ]
     ]
   }

**How it Works:** When ``pyDarwin`` builds a model, it iterates through
each token name (e.g., ``"TOKEN_NAME_1"``). It selects one of the option
arrays (e.g., the second option
``[ "text for option 2, index 1" , "text for option 2, index 2" ]``).

Then, when it encounters a placeholder in the template like
``{TOKEN_NAME_1[index]}``, it uses the index to pick the corresponding
string from the selected option array.

-  ``{TOKEN_NAME_1[1]}`` would be replaced with
   ``"text for option 2, index 1"``.
-  ``{TOKEN_NAME_1[2]}`` would be replaced with
   ``"text for option 2, index 2"``.

**The "Off" State:** A crucial convention is to make the *first option*
for each token the "off" or "base" state. This is typically an array of
empty strings (``[ "", "" ]``). This ensures that there is always a
baseline model generated where none of the optional features are added.

**Complete pyDarwin Search Example**

This example demonstrates a search to test for the effect of Body Weight
(``BW``) on the clearance (``Cl``) of a one-compartment IV bolus model.

``template.mmdl``

::

   ##Description: 1-Cpt IV Bolus with BW on Cl search
   ##DATA {data_dir}/pk_data.csv
   ##MAP A1 = Dose CObs = DV BW = BW id = ID time = time
   ##MODEL
   test() {
     cfMicro(A1, Cl / V)
     C = A1 / V
     dosepoint(A1, idosevar = A1Dose)
     error(CEps = 0.1)
     observe(CObs = C * (1 + CEps))
     fcovariate(BW)

     # Token to modify the Cl equation
     stparm(Cl = tvCl {_COV_Cl[1]} * exp(nCl))
     stparm(V = tvV * exp(nV))
     
     fixef(tvCl = c(, 1, ))
     fixef(tvV = c(, 10, ))
     # Token to add the fixef for the covariate effect
     {_COV_Cl[2]}
     
     ranef(diag(nCl, nV) = c(1, 1))
   }

``tokens.json``

.. code:: json

   {
     "_COV_Cl": [
       [
         "",
         ""
       ],
       [
         " * (BW/70)^dBWdCl",
         "\n\tfixef(dBWdCl = c(, 0.75, ))"
       ]
     ]
   }

**Workflow Explanation:** ``pyDarwin`` will generate two models from
these files:

1. **Model 1 (Covariate Off):**

   -  It selects the first option from ``_COV_Cl``: ``["", ""]``.
   -  ``{_COV_Cl[1]}`` is replaced with an empty string. The ``stparm``
      becomes ``stparm(Cl = tvCl * exp(nCl))``.
   -  ``{_COV_Cl[2]}`` is replaced with an empty string. No extra
      ``fixef`` is added.

2. **Model 2 (Covariate On):**

   -  It selects the second option from ``_COV_Cl``.
   -  ``{_COV_Cl[1]}`` is replaced with ``" * (BW/70)^dBWdCl"``. The
      ``stparm`` becomes
      ``stparm(Cl = tvCl * (BW/70)^dBWdCl * exp(nCl))``.
   -  ``{_COV_Cl[2]}`` is replaced with
      ``"\n\tfixef(dBWdCl = c(, 0.75, ))"``, adding the necessary fixed
      effect definition.

The results of these two runs can then be compared to determine if
including Body Weight as a covariate on Clearance significantly improves
the model fit.

**Keywords:** tokens.json, JSON, key, search space, array of arrays, options, pyDarwin

**See also:** Introduction to pyDarwin Integration, The Metamodel as a Template File


Directory Shortcuts in Templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``pyDarwin`` supports special directory shortcuts within
the metamodel template file. These shortcuts, such as ``{data_dir}``,
act as placeholders for directory paths. This allows templates to be
highly portable, as the actual paths are provided as arguments when the
``pyDarwin`` search is executed, rather than being hard-coded into the
template itself.

Hard-coding the full path to a dataset within a metamodel
template (e.g., ``##DATA C:/MyProject/data/pk_data.csv``) makes the
template difficult to share and reuse. Directory shortcuts solve this
problem by parameterizing the paths.

**Example:** The most frequent use of these shortcuts is in the
``##DATA`` block to specify the location of the input dataset.

**Hard-coded (less portable) example:**

::

   ##DATA C:/Users/Me/MyProject/data/warfarin_data.csv

**Using a shortcut (recommended, portable):**

::

   ##DATA {data_dir}/warfarin_data.csv

**Keywords:** data_dir, work_dir, output_dir, directory shortcut, path, parameterization, portable

**See also:** The Metamodel as a Template File, ##DATA Block, ##TABLES Block


The pyDarwin Execution Options File
------------------------------------------------------------------------

To execute a ``pyDarwin`` search with the NLME engine, the
``options.json`` file must specify the correct ``engine_adapter`` and
provide the paths to the NLME installation and its required compiler.
Other core options control the search algorithm, the degree of
parallelism, and the penalties applied to model fitness scores.

The following options form the fundamental configuration
for any ``pyDarwin`` run that uses the NLME engine.

-  ``engine_adapter``: **(Required)** This critical option tells
   ``pyDarwin`` which modeling engine to use. For NLME, it must be set
   to ``"nlme"``.

   -  **Example:** ``"engine_adapter": "nlme"``

-  ``nlme_dir``: **(Required)** The absolute file path to the NLME
   Engine installation directory.

   -  **Example:**
      ``"nlme_dir": "C:/Program Files/Certara/NLME_Engine"``

-  ``gcc_dir``: **(Required)** The absolute file path to the root
   directory of the GCC compiler used by the NLME Engine.

   -  **Example:** ``"gcc_dir": "C:/Program Files/Certara/mingw64"``


pyDarwin Best Practices
------------------------------------------------------------------------

The Golden Rules of Metamodel Templates for pyDarwin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To ensure ``pyDarwin`` can correctly parse and process
metamodel templates, several strict formatting rules MUST be followed.
Violating these rules can lead to silent parsing errors or incorrect
model generation. This entry serves as a critical checklist.

The following formatting rules are not optional; they are required for creating valid and robust ``pyDarwin`` templates.

**1.** ``##DATA`` **Block MUST Be a Single Line** The path to the data file
must be on the same line as the ``##DATA`` keyword.

-  **Correct:**
   ::

      ##DATA {data_dir}/my_data.csv

-  **Incorrect:**
   ::

      ##DATA
        {data_dir}/my_data.csv

**2.** ``##MAP`` **Block MUST Be a Single Line** All column mappings in a
``##MAP`` block must be on the same line as the ``##MAP`` keyword,
separated by spaces or commas.

-  **Correct:**
   ::

      ##MAP id=Subject time=Time CObs=DV

-  **Incorrect:**
   ::

      ##MAP
        id = Subject
        time = Time
        CObs = DV

**3. No Comments Within** ``##DATA`` **and** ``##MAP`` **Blocks** Because these
blocks must be single lines, do not attempt to add comments on the same
line.

-  **Correct:**
   ::

      ##Description: Model for study XYZ
      ##DATA ./data.csv
      ##MAP id=ID

-  **Incorrect:**
   ::

      ##DATA ./data.csv # Path to the dataset
      ##MAP id=ID # Subject identifier

**4. Do NOT Place Token Syntax Inside Comments** This is a
frequent source of errors. The ``pyDarwin`` parser may attempt to
substitute tokens found within comments, leading to unpredictable
results. A comment should describe the *purpose* of a tokenized section,
but the token syntax itself (``{TOKEN[index]}``) must never appear
inside the comment.

-  **Correct:**
   .. code:: pml

      # Token for the structural model differential equations.
      {_STRUCT[1]}

-  **Incorrect:**
   .. code:: pml

      # The {_STRUCT[1]} token defines the differential equations.
      {_STRUCT[1]}

**Keywords:** golden rules, best practices, checklist, template, syntax, ##DATA, ##MAP, comments, tokens, pyDarwin, formatting

**See also:** The Metamodel as a Template File, Introduction to pyDarwin Integration


Automated Search of Omega Structure
------------------------------------------------------------------------

Searching Omega Structure in NLME Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``pyDarwin`` can automatically search for the optimal
variance-covariance (Omega) matrix structure for random effects. It can
test models with a simple diagonal matrix against models with various
block-diagonal structures. This search is controlled by an option in
``options.json`` and a special ``#search_block`` directive in the
metamodel template.

Instead of manually creating different models to test for
correlations between random effects, you can instruct ``pyDarwin`` to
explore these structures automatically.

.. _1-basic-omega-block-search:

**Basic Omega Block Search**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the most common use case, where you want to test if a set of
random effects should be modeled as independent (diagonal matrix) or
correlated (a single block matrix).

**To enable a basic block search, you must do two things:**

**Step 1: Add the** ``#search_block`` **Directive to Your Template**

In your metamodel template (``.mmdl`` file), add a special comment line
with the syntax ``#search_block(randomEffect1, randomEffect2, ...)``.
This tells ``pyDarwin`` which random effects are candidates for the
block-diagonal search.

-  This directive can be placed anywhere in the ``##MODEL`` block, but
   it is good practice to place it near the ``ranef`` statements.
-  The random effects listed inside the parentheses must correspond to
   names used in a ``ranef`` statement that defines them with a
   **diagonal** structure.

**Step 2: Enable the Search in** ``options.json``

In your ``options.json`` file, add the following key-value pair:
``"search_omega_blocks": true``

**How It Works: An Example**

Imagine your metamodel template has the following ``ranef`` statement
and ``search_block`` directive:

.. code:: pml

   # template.mmdl snippet
   ...
   ranef(diag(nCl, nV) = c(0.09, 0.09))
   #search_block(nCl, nV)
   ...

And your ``options.json`` contains ``"search_omega_blocks": true``.

``pyDarwin`` will automatically generate and test **two** different
models:

1. **Model 1 (Diagonal):** The ``ranef`` statement is left as is,
   modeling no correlation.

   .. code:: pml

      ranef(diag(nCl, nV) = c(0.09, 0.09))

2. **Model 2 (Block):** ``pyDarwin`` automatically creates a
   block-diagonal structure for the searched effects.

   .. code:: pml

      ranef(block(nCl, nV) = c(0.09, 0, 0.09))

**Important Rules and Restrictions:**

-  The ``#search_block`` directive must only contain a comma-separated
   list of random effect names. No other comments or syntax are allowed
   inside the parentheses.
-  Only random effects defined in a ``diag()`` context can be
   included in a ``#search_block``. You cannot search effects that are
   already part of a ``block()``, ``same()``, or ``fixed`` structure.
-  If a random effect is dependent on another (e.g.,
   ``ranef(diag(nCl), same(nOther))``), you cannot include ``nCl`` in
   the search block.

.. _2-advanced-search-with-submatrices:

**Advanced Search with Submatrices**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This feature expands the search beyond the simple "all diagonal vs. one
big block" paradigm. It allows ``pyDarwin`` to test various combinations
of smaller block matrices within the searched effects, which can be
useful for identifying specific correlation patterns without
over-parameterizing the model.

**To enable a submatrix search, add two options to** ``options.json``

1. ``"search_omega_sub_matrix": true``
2. ``"max_omega_sub_matrix": N``, where ``N`` is an integer for the
   maximum size of any sub-block to be considered (e.g., 2 or 3).

**How It Works: An Example**

Consider a search on four random effects:

.. code:: pml

   # template.mmdl snippet
   ranef(diag(nCl, nV, nKa, nF) = c(1,1,1,1))
   #search_block(nCl, nV, nKa, nF)

And your ``options.json`` contains:

.. code:: json

   "search_omega_blocks": true,
   "search_omega_sub_matrix": true,
   "max_omega_sub_matrix": 2

``pyDarwin`` will now test a much larger set of possible Omega
structures. In addition to the full diagonal and the single 4x4 block,
it will also test patterns like:

-  **Pattern A: One 2x2 block**

   .. code:: pml

      ranef(block(nCl, nV) = c(1,0,1))
      ranef(diag(nKa, nF) = c(1,1))

-  **Pattern B: A different 2x2 block**

   .. code:: pml

      ranef(diag(nCl) = c(1))
      ranef(block(nV, nKa) = c(1,0,1))
      ranef(diag(nF) = c(1))

-  **Pattern C: Two separate 2x2 blocks**

   .. code:: pml

      ranef(block(nCl, nV) = c(1,0,1))
      ranef(block(nKa, nF) = c(1,0,1))

...and all other valid combinations. ``pyDarwin`` automatically
generates this entire search space of patterns based on the parameters
in the ``#search_block`` and the ``max_omega_sub_matrix`` setting.

**Keywords:** Omega search, search_omega_blocks, #search_block, ranef,
block, diag, search_omega_sub_matrix, max_omega_sub_matrix, pyDarwin,
NLME, variance-covariance

**See also:** The options.json File, The Metamodel as a Template File, ranef
