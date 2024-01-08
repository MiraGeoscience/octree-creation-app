.. _methodology:

Methodology
===========

This section provides technical details regarding the algorithm used for the
creation octree meshes. The entire process can be broken down into two main parts:

- `General Parameters (Mesh extents) <mesh_creation>`_: Define the outer limits of the mesh and the core cell size.
- `Optional Parameters (Refinements) <refinement>`_: Refine the mesh based on a set of rules.

.. _mesh_creation:

Mesh extents
------------

The general parameters control the core parameters that define the position and extent of mesh. This step relies on the
`discretize.utils.mesh_builder_xyz <http://discretize.simpeg.xyz/en/main/api/generated/discretize.utils.mesh_builder_xyz.html?highlight=xyz#discretize-utils-mesh-builder-xyz>`_
method to create the mesh.


.. figure:: /images/extent_parameters.png
    :scale: 100%


- **Core hull extent**: List of objects available to define the core region extent.

- **Core cell size**:
    - *Easting (m)*: Smallest cell size along East-West axis, in meters.
    - *Northing (m)*: Smallest cell size along North-South axis, in meters.
    - *Vertical (m)*: Smallest cell size along vertical acis, in meters.

- **Depth Core**: Thickness of the mesh added below the lowest point of the

- **Minimum Refinement**:

    Largest octree level allowed after refinement.
    The equivalent cell dimension =

    .. math::

        h \times 2^{level}

    where *h* is the *core cell size* in a given direction.

Example
^^^^^^^

The example below demonstrates this process with simple line survey shown below and the following parameters:

.. image:: images/octree_padding_distance.png
  :scale: 100%
  :alt: paddings


Horizontal extent
#################

    - Input:
        - 5,600 m (survey hull)
        - 2 * 1,000 m (padding distance)

        **Total: 7,600 m**

    - Number of cells:

        .. math::

            \frac{7,600 \;m}{25 \; m/cell} = 304 \; cells \\

        **Round up -> 512 cells**

    - Final dimensions:

        512 cells * 25 m/cell = 12,800 m


Vertical extent
###############

    - Input dimensions:
        - 46 m (survey hull)
        - 2*1000 m (vertical padding)
        - 500 m (depth core)

        **Total: 2,546 m**

    - Number of cells
        .. math::

            \frac{2546 \; m}{25\; \frac{m}{cell}} = 102\; cells \\

        **Round up -> 128 cells**

    - Final dimensions:
        .. math::

            128 \; cells * 25 \frac{m}{cell} = 3,200\;m

Minimum refinement
##################

    - Input:
        - 25 m (core cell size)
        - 5 (minimum refinement)

    **Largest cell dimension: 25 m * 2^5 = 800 m**


The final mesh expected would be a 512 x 512 x 128 cells mesh, with an extent of 12,800 x 12,800 x 3,200 m. Note that the
cell size is uniform and equal to the minimum level of 5, as defined in the parameters.


.. _refinements:

Refinements
-----------

Once the extent of the mesh has been defined, the program can proceed with refinement of the mesh.
The following section describe the different refinement strategies available.


Refine from points
------------------

.. automethod:: octree_creation_app.driver.OctreeDriver.refine_tree_from_points

This method refines an octree mesh radially from the vertices of an object.

.. image:: images/octree_radial.png
  :width: 400
  :alt: radial


Refine from curve
-----------------

.. automethod:: octree_creation_app.driver.OctreeDriver.refine_tree_from_curve

This method refines an octree mesh along the segments of a curve object.


Refine from surface
-------------------

.. automethod:: octree_creation_app.driver.OctreeDriver.refine_tree_from_surface

This method refines an octree mesh along a surface. It is a faster
implementation then the `Refine from triangulation`_ method, but it assumes the surface
to be mostly horizontal (z-normal). It is especially useful for refining meshes along topography.

.. image:: images/octree_surface.png
  :width: 400
  :alt: surface


Refine from triangulation
-------------------------

.. automethod:: octree_creation_app.driver.OctreeDriver.refine_tree_from_triangulation

The function is used to refine an octree mesh on a triangulated surface in 3D. It is
especially useful for refining meshes along geological features, such as faults and geological contacts.
