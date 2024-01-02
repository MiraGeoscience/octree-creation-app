.. _usage:

Basic usage
===========

The main entry point is the ui.json (stored under ``assets``) for the octree-creation application that can be rendered by Geoscience ANALYST.
The interface has two sections:

 - :ref:`Core parameters <General Parameters>`
 - :ref:`Optional Parameters <Optional Parameters>`


ui.json interface
~~~~~~~~~~~~~~~~~

The ui.json interface has two sections:

.. _General Parameters:

1. General Parameters
_____________________

The general parameters control the core parameters that define the position and extent of mesh.

.. figure:: /images/ui_json.png
    :scale: 40%


- *Core hull extent*: List of objects available to define the core region extent.
- *Core cell size*:
    - *Easting (m)*: Smallest cell size along East-West axis, in meters.
    - *Northing (m)*: Smallest cell size along North-South axis, in meters.
    - *Vertical (m)*: Smallest cell size along vertical acis, in meters.
- *Depth Core*: Thickness of the mesh added below the lowest point of the
- *Minimum Refinement*: Largest octree level allowed after refinement.
    The equivalent cell dimension =

    .. math::

        h \times 2^{level}

    where $h$ are the *core cell size*


.. _Optional Parameters:

2. Refinement Parameters
________________________


The second tab defines the refinement strategies applied to the mesh.
