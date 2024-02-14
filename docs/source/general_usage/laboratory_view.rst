Vista de laboratorio
*****************************

Crear objeto en el estante
================================

De tipo reactivo
---------------------

1. Reactivo con contenedor clonado
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ../_static/gif/create_shelfobject_reactive_with_clone_container.gif
   :height: 380
   :width: 720


2. Reactivo con contenedor seleccionado
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ../_static/gif/create_shelfobject_reactive_with_use_selected_container.gif
   :height: 380
   :width: 720


De tipo material
---------------------

.. image:: ../_static/gif/create_shelfobject_material.gif
   :height: 380
   :width: 720


De tipo equipo
---------------------

.. image:: ../_static/gif/create_shelfobject_equipment.gif
   :height: 380
   :width: 720



Acciones del objeto en el estante
======================================

Ver detalle del objeto en el estante
-----------------------------------------------

.. image:: ../_static/gif/view_shelfobject_detail.gif
   :height: 380
   :width: 720



Reservar un objeto en el estante
-----------------------------------------------

.. image:: ../_static/gif/reserve_shelfobject.gif
   :height: 380
   :width: 720


Incrementar un objeto en el estante
-----------------------------------------------

.. image:: ../_static/gif/increase_shelfobject.gif
   :height: 380
   :width: 720


Transferir un objeto en el estante a otro laboratorio
------------------------------------------------------------

.. image:: ../_static/gif/transfer_out_shelfobject.gif
   :height: 380
   :width: 720


Transferir un objeto en el estante como desecho a otro laboratorio
--------------------------------------------------------------------------

.. image:: ../_static/gif/transfer_out_shelfobject_refuse.gif
   :height: 380
   :width: 720


Decrementar un objeto en el estante
------------------------------------------

.. image:: ../_static/gif/decrease_shelfobject.gif
   :height: 380
   :width: 720


Actualizar contenedor del objeto en el estante (Reactivo)
-------------------------------------------------------------------------


1. Opciones de contenedor --> Crear nuevo basado en el seleccionado
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ../_static/gif/manage_shelfobject_container_clone.gif
   :height: 380
   :width: 720


2. Opciones de contenedor --> Usar seleccionado
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ../_static/gif/manage_shelfobject_container_available.gif
   :height: 380
   :width: 720


Mover un objeto en el estante a otro estante (Dentro del mismo laboratorio)
---------------------------------------------------------------------------------------------

1. Opciones de contenedor --> Crear nuevo basado en el seleccionado
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ../_static/gif/move_shelfobject_with_clone_container.gif
   :height: 380
   :width: 720


2. Opciones de contenedor --> Usar seleccionado
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ../_static/gif/move_shelfobject_with_available_container.gif
   :height: 380
   :width: 720


3. Opciones de contenedor --> Mover el contenedor desde el laboratorio fuente
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ../_static/gif/move_shelfobject_with_use_source_container.gif
   :height: 380
   :width: 720


4. Opciones de contenedor --> Crear uno nuevo a partir del contenedor actual en el laboratorio fuente
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ../_static/gif/move_shelfobject_with_new_based_source_container.gif
   :height: 380
   :width: 720


Ver la bitácora de un objeto en el estante
--------------------------------------------------------

.. image:: ../_static/gif/view_shelfobject_logs.gif
   :height: 380
   :width: 720


Descargar PDF de la información de un objeto en el estante
---------------------------------------------------------------------

.. image:: ../_static/gif/download_shelfobject_info.gif
   :height: 380
   :width: 720


Eliminar un objeto en el estante
---------------------------------------------------------------------

.. image:: ../_static/gif/delete_shelfobject.gif
   :height: 380
   :width: 720


Eliminar un objeto en el estante y su contenedor
---------------------------------------------------------------------

.. image:: ../_static/gif/delete_shelfobject_and_its_container.gif
   :height: 380
   :width: 720




Búsqueda de elementos
=========================================================

La sección de búsqueda presenta las siguientes características:


Permisos de usuario
--------------------------

    Verifica permisos de usuario en el laboratorio y la organización. En caso de que el usuario en sesión
    no tenga permisos en el laboratorio y organización actual, este será redireccionado a la página de inicio
    de sesión como permiso denegado 403.


    .. image:: ../_static/user_without_permissions.png


Partes del campo de búsqueda
--------------------------------------

    .. image:: ../_static/search_input.png


    Permite filtrar y seleccionar etiquetas de laboratorio como salas de laboratorio, muebles, estantes, objetos
    en el estante y objetos.


    .. image:: ../_static/search.png

Botones de acción
-----------------

    Estos botones están incluidos dentro de la funcionalidad de búsqueda.


    .. image:: ../_static/collapse_button.png
    .. image:: ../_static/search_action_buttons.png

 - ``Botón de colapso (Primer botón --> ícono de comprimir)``: Colapsa el árbol relacional de elementos.
    .. image:: ../_static/collapse_button.png

 - ``Botón para remover todas las etiquetas (Segundo botón --> ícono de bote de basura)``: Remueve todas las etiquetas
    dentro del campo de búsqueda y reinicia los elementos de búsqueda (árbol relacional).
    .. image:: ../_static/remove_all_tags.png

 - ``Botón de información del color (Tercer botón --> ícono de información)``: Brinda información acerca de las
    etiquetas de elementos de filtro dentro del laboratorio con su respectivo color.

    .. image:: ../_static/color_info.png


Tipo de búsqueda por elemento
------------------------------------

Buscar por sala de laboratorio
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Permite encontrar y seleccionar la sala respectiva dentro del laboratorio.

   .. image:: ../_static/search_labroom.png


Buscar por mueble
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Permite encontrar y seleccionar el mueble respectivo dentro del laboratorio. Además su antecesor
    (La sala de laboratorio que lo contiene) también será seleccionado en el árbol de relación.

    .. image:: ../_static/search_furniture.png

Buscar por estante
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    It allows to relate and find a specific shelf inside a laboratory. Shelf element and its
    predecessors(furniture, laboratory room) will be selected and shelf object table is going to be update by this shelf.

    Permite encontrar y seleccionar el estante respectivo dentro del laboratorio. Además sus antecesores
    (La sala de laboratorio y su mueble que lo contienen) también serán seleccionados en el árbol de relación.
    La tabla que se ubica en la parte inferior de la vista de laboratorio que contiene los objetos en el estante también
    será actualizada una vez se haya procedido con la búsqueda efectiva del estante por medio del uso de las etiquetas.

    .. image:: ../_static/search_shelf.png


Buscar por objeto en el estante
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Permite encontrar y seleccionar el objeto en el estante respectivo dentro del laboratorio. Además sus antecesores
    (La sala de laboratorio, su mueble y su estante que lo contienen) también serán seleccionados en el árbol de relación.
    La tabla que se ubica en la parte inferior de la vista de laboratorio que contiene los objetos en el estante también
    será actualizada por la selección del estante y en la tabla se agregará en el campo de búsqueda "pk=ID DEL OBJETO EN EL ESTANTE",
    este ID corresponderá al elemento de la etiqueta seleccionado.


    .. image:: ../_static/search_shelfobject.png

Buscar por objeto
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Permite encontrar coincidencias con objetos ubicados en distintos estantes, muebles y salas.
    La búsqueda de objetos solo incluirá los que están registrados en stock por lo que si se ingresa
    el nombre de uno que no hay a disposición en el laboratorio el resultado de tags no mostrará resultados.
    El primer elemento del resultado será el seleccionado y filtrado en la tabla de objetos en el estante.

   .. image:: ../_static/search_object1.png
   .. image:: ../_static/search_object2.png


Buscar por enlace
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Esta función obtiene los siguientes parámetros: [sala de laboratorio, mueble, estante, objeto en el estante],
    los cuales no son parámetros requeridos en esta vista, solamente representan una búsqueda alternativa y opcional.
    Uno de los requisitos es que exista relación entre los elementos que el enlace incluya.

    Un ejemplo de esto es la siguiente dirección de enlace ``{{domain}}/lab/1/1/rooms/?labroom=1&furniture=1`` donde
    ``furniture 1`` pertenece a ``labroom 1``. Además cualquier elemento declarado en el enlace debe encontrarse dentro
    del laboratorio.

   .. image:: ../_static/search_by_url.png


Clasificación de la prioridad de búsqueda
----------------------------------------------

 Los elementos dentro de la vista de laboratorio serán clasificados bajo el siguiente orden de prioridad:

 - 1. ``Objeto``
 - 2. ``Objeto en el estante``
 - 3. ``Estante``
 - 4. ``Mueble``
 - 5. ``Sala de laboratorio``

 El elemento objeto será el de mayor prioridad mientras que la sala de laboratorio tendrá la menor prioridad en esta clasificación.

 Un ejemplo es una búsqueda con etiquetas multiples como las siguientes:

 ``Inventory Room (Laboratory Room)``  ``Nitrogen(Object)``


 El buscador encontrará ambos elementos, pero el segundo al ser un elemento de tipo objeto tendrá mayor prioridad
 sobre la búsqueda. En la siguiente imagen adjuntada se puede apreciar que el tag de ``Inventory Room`` fue
 seleccionado y su resultado fue filtrado por la sala de laboratorio y oculta los otros, pero no obstante la segunda
 etiqueta ``Nitrogen`` busca un objeto en específico, el cual fue encontrado dentro de ``Inventory Room`` y ``Test Room``
 por defecto este elemento será seleccionado como un antecesor.

    .. image:: ../_static/priority_search.png

