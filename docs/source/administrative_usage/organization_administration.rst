Descripción general del manejo de organización
**************************************************

/perms/organization/manage/

Crear nueva organización base
================================

/organization/create

Cuando se menciona una organizacion base, se hace referencia a la organización raíz (sin antecesor) y que por
consiguiente tendrá futuro organizaciones descendientes (organizaciones hijas) o en casos menos comunes no solo será la
organización (organizaciones únicas sin antecesor, ni sucesores).

Permisos requeridos:

* **"view_organizationstructure"**: para visualizar el menú de gestión organizaciones.
* **"change_organizationstructure"**: para ingresar a la vista de gestión de organizaciones.
* **"add_organizationstructure"**: para apreciar el botón relacionado al agregado de una organization base y por consiguiente realizar la acción.


.. video:: ../_static/manage_organization/organization/video/crear_organizacion_base.mp4
   :height: 400
   :width: 600


Crear nueva organización hija
==================================

/organization/create

Las organizaciones hijas pueden tener organizaciones descendientes y siempre tendrán una organización base antecesora,
sin embargo esto puede cambiar si existe la necesidad de convertir una organización hija a una organización base se
puede realizar.


Permisos requeridos:

* **"view_organizationstructure"**: para visualizar el menú de gestión organizaciones.
* **"change_organizationstructure"**: para ingresar a la vista de gestión de organizaciones.
* **"add_organizationstructure"**: para apreciar el botón relacionado al agregado de una organization base y por consiguiente realizar la acción.


.. video:: ../_static/manage_organization/organization/video/crear_organizaciones_descendientes.mp4
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
