Descripción general del manejo de organización
**************************************************

Permisos requeridos:

* *view_organizationstructure*: Permite visualizar el item **"Administración de Organizaciones"** en el menú de la barra lateral.
* *change_organizationstructure*: Autoriza el ingreso a la vista de **"Administración de Organizaciones"**.
* *add_organizationstructure*: Muestra los botones **"Agregar Organización"** y **"+"** que permiten realizar la acción del agregado de organizaciones base y organizaciones hijas.
* *delete_organizationstructure*: Muestra el botón de eliminar organización **"-"** y por consiguiente permite realizar la acción del eliminado de organizaciones.


Crear nueva organización base
================================

Cuando se menciona una organización base, se hace referencia a la organización raíz (sin antecesor) y que por
consiguiente tendrá a futuro organizaciones descendientes (organizaciones hijas) o en casos menos comunes solo será la
organización (organización única sin antecesor, ni sucesores).

.. video:: ../_static/manage_organization/organization/video/create_base_organization.mp4
   :height: 400
   :width: 600



La organización base es la más conveniente a la hora de agregar laboratorios dado que se pueden relacionar estos con sus organizaciones hijas.




Crear nueva organización hija
==================================

Las organizaciones hijas pueden tener organizaciones descendientes y siempre tendrán una organización base antecesora.

.. video:: ../_static/manage_organization/organization/video/create_descendants_organizations.mp4
   :height: 400
   :width: 600



Cambiar padre de una organización
=============================================

.. video:: ../_static/manage_organization/organization/video/change_organization_parent.mp4
   :height: 400
   :width: 600



Eliminar una organización
============================

/organization/<int:org>/delete


Actualizar una organización
=======================================

Permite cambiar el nombre y la organización padre
/organization/42/update

Administración de usuarios
******************************

Linkear a la sección de crear un usuario en una organización.

Relacionar un usuario a una organización
============================================

Indicar cómo se relaciona un usuario a una organización


Ver bitácoras de acciones en la organización
====================================================

/logentry/<int:org>


Acciones de gestión de organización
============================================
