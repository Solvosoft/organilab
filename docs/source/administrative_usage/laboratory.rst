Laboratory administration
*******************************

Crear un laboratorio en una organización
===========================================

.. video:: ../_static/manage_organization/organization/video/create_laboratory_in_organization.mp4
   :height: 400
   :width: 600

Relacionar un laboratorio a una organización
=================================================

Explicar que es relacionar un laboratorio a una organización


Administración de sala de laboratorio
=========================================

Creación de sala de laboratorio
-------------------------------------

/lab/<int:org>/<int:lab>/rooms/create

Creación de mueble
----------------------------

/lab/<int:org>/<int:lab>/furniture/create/<int:room>/


Administración de muebles
----------------------------

/lab/<int:org>/<int:lab>/furniture/edit/<int:room>/

Reconstrucción de QR
------------------------

/lab/<int:org>/<int:lab>/rooms/rebuild_laboratory_qr

Administración de objetos
=================================


Administración de Reactivos
-------------------------------

Acá poner el crear  y editar y explicar los íconos de la primera columna de la tabla


Administración de Materiales
------------------------------

/lab/<int:org>/<int:lab>/objects/list?type_id=1


Administración de Equipos
------------------------------

/lab/<int:org>/<int:lab>/objects/list?type_id=2

Administración de características de objetos
===============================================

Explicar para que sirve esta sección

/lab/<int:org>/<int:lab>/features/create/

Administración de proveedores
====================================

/lab/<int:org>/<int:lab>/provider/list/

Administración de protocolos
===============================

/lab/<int:org>/<int:lab>/protocols/create
