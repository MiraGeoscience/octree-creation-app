.. _usage:

Basic usage
===========

The main entry point is the ui.json (stored under ``assets``) for the octree-creation application that can be rendered
by Geoscience ANALYST. The interface has two sections:

 - :ref:`Mesh creation parameters <mesh_creation>`
 - :ref:`Refinement parameters <refinements>`

.. figure:: /images/ui_json.png
    :scale: 40%

From ANALYST Pro
----------------

At this point, you will have all required packages to run the applications.
 users can run the application with a **ui.json** file by drag-and-drop:

.. figure:: /images/getting_started/drag_and_drop.png
    :align: center
    :width: 75%

or by Python menu dropdown by placing a **ui.json** file
in the Python scripts folder.

**1.**

.. figure:: /images/getting_started/python_scripts_folder.png
    :align: center
    :width: 75%

**2.**

.. figure:: /images/getting_started/python_menu_uijson.png
    :align: center
    :width: 75%

**3.**

.. figure:: /images/getting_started/dropdown_scripts.png
    :align: center
    :width: 75%

Either operation will result in the rendering of a ui.json file within the
Geoscience ANALYST viewport.  To learn about the ui.json interface and how
to run the application in one of two modes, proceed to the
:ref:`Basic Usage <usage>` section.

From command line
-----------------

The application can also be run from the command line.  This is useful for more advanced users that may want to automate
the mesh creation process, or re-run an existing mesh with different parameters.  To run the application from the command line,

``python -m octree_creation_app.driver input_file.json``

where ``input_file.json`` is the path to the input file.
