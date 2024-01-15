Laboratory administration
===============================

Crear un laboratorio en una organización
----------------------------------------------

.. video:: ../_static/manage_organization/organization/video/create_laboratory_in_organization.mp4
   :height: 400
   :width: 600

Relacionar un laboratorio a una organización
----------------------------------------------

Explicar que es relacionar un laboratorio a una organización


Laboratory view
**********************************


Administración de cuartos de laboratorio
-------------------------------------------
/lab/<int:org>/<int:lab_pk>/create/
Este modulo se utiliza para el manejo de cuartos de laboratorios del laboratorio que se este utilizando en el momento,
para accede ha este modulo existen 2 formas en ambas se requiere el ingreso a un laboratorio, que se mostraran en las siguientes imagenes:

En el primer caso al ingresar al modulo de laboratorio, se debe dar click en la opcion **Laboratorio**

Ejemplo de la primeraa forma:
.. image:: ../_static/gif/view_room.gif

En el segundo caso se puede utilizar en diferentes modulos internos del laboratorio a diferencia del anterior,
por el hecho que trabaja con la barra superior, del cual a su vez se da click en la opción **Administracion**,
el cual desplega unas nuevas opciones de acceso donde se debe seleccionar **Administración de laboratorio** para ingresar
al modúlo de cuartos de laboratorio.

Ejemplo de segundo forma:

.. image:: ../_static/gif/view_room_navbar.gif

**Permisos Requeridos:**

*   view_laboratoryroom: Permite visualizar los cuartos que el laboratorio posee.
*   add_laboratoryroom: Permite la creacion de uno nuevo cuarto de laboratorio
*   change_laboratoryroom: Permite ingresar al modulo de actualizar cuarto y visualizar el botón de actualizar.
*   delete_laboratoryroom: Permite eliminar cuarto y visualizar el botón de eliminar.
*   add_furniture: Permite crear un mueble en el cuarto de laboratorio y que se visualize el botón de creación.
*   view_furniture: Permite visualizar los muesble del cuarto de laboratorio.
*   change_furniture: Permite ingresar al modula de edicion de mueble del cuarto y actualizarlos.


Crear cuarto de laboratorio
**********************************
/lab/<int:org>/<int:lab_pk>/create/

Este modulo crearan cuartos de labororios del laboratorio que se esta utilizando, en estos cuartos normalmente se le asocian
muebles, estantes, objectos entre otras mas temas.

Datos Requeridos:

*   **Nombre:** Este campo registra el nombre del cuarto del laboratorio.

Permisos requeridos:

*   view_laboratoryroom: Permite visualizar los cuartos que el laboratorio posee.
*   add_laboratoryroom: Permite la creacion de uno nuevo cuarto de laboratorio.

Ejemplo de creacion de cuarto de laboratorio:

.. image:: ../_static/gif/add_room.gif


Actualizar cuartos de laboratorios
***********************************
/lab/<int:org>/<int:lab_pk>/rooms/<int:pk>/edit

Este modulo actualizara el nombre de los cuartos de laboratorio.

Datos Requeridos:

*   **Nombre:** Este campo registra el nombre del cuarto del laboratorio.

Permisos requeridos:

*   view_laboratoryroom: Permite visualizar los cuartos que el laboratorio posee.
*   change_laboratoryroom: Permite la creacion de uno nuevo cuarto de laboratorio.

Ejemplo de actualización de cuarto de laboratorio:
.. image:: ../_static/gif/update_room.gif


Eliminar cuarto de laboratorio
**********************************
/lab/<int:org>/<int:lab_pk>/rooms/<int:pk>/delete

En este punto se permitira eliminar cuartos de laboratorio.
    .. note::
        Al momento de eliminar un cuarto de laboratorio, a su vez eliminara todos los muebles y estantes vinculados a esté.

Datos Requeridos:

*   Acceder a un laboratorio previamente.

Permisos requeridos:

*   view_laboratoryroom: Permite visualizar los cuartos que el laboratorio posee.
*   delete_laboratoryroom: Permite eliminar el cuarto de laboratorio elegido.


Ejemplo de eliminacion de cuartos de laboratorios:

.. image:: ../_static/gif/delete_room.gif


Visualizar cuarto de laboratorio
**********************************
/lab/<int:org>/<int:lab_pk>/create/

Este modulo permitira visualizar el listado de cuartos de laboratorio del laboratorio que este actualimente utilizando.

Datos Requeridos:

*   Acceder a un laboratorio previamente.

Permisos requeridos:

*   view_laboratoryroom: Permite visualizar los cuartos que el laboratorio posee.

Ejemplo de visualizar de cuartos de laboratorio:

.. image:: ../_static/gif/view_room.gif




Creación de sala de laboratorio
**********************************

/lab/<int:org>/<int:lab>/rooms/create

Creación de mueble
**********************************

/lab/<int:org>/<int:lab>/furniture/create/<int:room>/


Administración de muebles
**********************************

/lab/<int:org>/<int:lab>/furniture/edit/<int:room>/

Reconstrucción de QR
**********************************

/lab/<int:org>/<int:lab>/rooms/rebuild_laboratory_qr

Administración de objetos
-------------------------------------------


Administración de Reactivos
**********************************

Acá poner el crear  y editar y explicar los íconos de la primera columna de la tabla


Administración de Materiales
**********************************

/lab/<int:org>/<int:lab>/objects/list?type_id=1


Administración de Equipos
**********************************

/lab/<int:org>/<int:lab>/objects/list?type_id=2

Administración de características de objetos
-----------------------------------------------

Explicar para que sirve esta sección

/lab/<int:org>/<int:lab>/features/create/

Administración de proveedores
-------------------------------------------

/lab/<int:org>/<int:lab>/provider/list/

Administración de protocolos
-------------------------------------------

/lab/<int:org>/<int:lab>/protocols/create
