Descripción general del manejo de organización
==================================================

Permisos requeridos:

* *view_organizationstructure*: Permite visualizar el item **"Administración de Organizaciones"** en el menú de la barra lateral.
* *change_organizationstructure*: Autoriza el ingreso a la vista de **"Administración de Organizaciones"**.
* *add_organizationstructure*: Muestra los botones **"Agregar Organización"** y **"+"** que permiten realizar la acción del agregado de organizaciones base y organizaciones hijas.
* *delete_organizationstructure*: Muestra el botón de eliminar organización **"-"** y por consiguiente permite realizar la acción del eliminado de organizaciones.


Crear nueva organización base
----------------------------------

Cuando se menciona una organización base, se hace referencia a la organización raíz (sin antecesor) y que por
consiguiente tendrá a futuro organizaciones descendientes (organizaciones hijas) o en casos menos comunes solo será la
organización (organización única sin antecesor, ni sucesores).

.. image:: ../_static/gif/create_org.gif
   :height: 400
   :width: 600



La organización base es la más conveniente a la hora de agregar laboratorios dado que se pueden relacionar estos con sus organizaciones hijas.



Crear nueva organización hija
----------------------------------

Las organizaciones hijas pueden tener organizaciones descendientes y siempre tendrán una organización base antecesora.

.. image:: ../_static/gif/add_org_descendant.gif
   :height: 400
   :width: 600


Cambiar padre de una organización
---------------------------------------

.. video:: ../_static/manage_organization/organization/video/change_organization_parent.mp4
   :height: 400
   :width: 600


Eliminar una organización
----------------------------------

Al eliminar una organización es necesario tener en cuenta si ésta tiene o no organizaciones hijas
(organizaciones descendientes) debido a que también las organizaciones hijas serán eliminadas.

.. image:: ../_static/gif/delete_org.gif
   :height: 400
   :width: 600


Acciones de una organización
----------------------------------

Las acciones de una organización son las siguientes:

* Desactivar organización
* Clonar organización
* Cambiar nombre de la organización


Desactivar una organización
*******************************

Solamente las organizaciones sin hijos pueden desactivarse y contemplarán las siguientes características:

* No se les puede agregar organizaciones hijas.
* Se pueden visualizar las bitácoras.
* No se puede cambiar su padre.
* No se pueden gestionar las acciones (desactivar organización, cambiar el nombre de la organización)
* Si se puede clonar la organización.
* No se puede activar nuevamente la organización.


.. image:: ../_static/gif/deactivate_org.gif
   :height: 400
   :width: 600


Clonar una organización
*******************************

.. image:: ../_static/gif/clone_org.gif
   :height: 400
   :width: 600


Cambiar nombre de una organización
***************************************

.. image:: ../_static/gif/clone_org.gif
   :height: 400
   :width: 600


Administración de usuarios
----------------------------------

Linkear a la sección de crear un usuario en una organización.

Relacionar un usuario a una organización
---------------------------------------------

Indicar cómo se relaciona un usuario a una organización


Ver bitácoras de acciones en la organización
--------------------------------------------------

/logentry/<int:org>


Acciones de gestión de organización
-----------------------------------------
