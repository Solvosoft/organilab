Administrar procedimientos
==========================================

Administrar plantillas de procedimientos
-------------------------------------------
/academic/<int:org>/procedure/procedure_list/

Para acceder a este modulo se requieren varios paso que se va a mostrar en las siguientes imagenes:

.. image:: ../_static/procedure/images/first_step_to_view_procedure_template.jpg
    :width: 700
    :height: 400

Explicacion de pasos:

*  *Paso 1*: Es dar click en la opción organizaciones de la barra lateral izquierda,  porque es necesario haber accesado en una organización.
*  *Paso 2*: En este paso se muestra un selector con un listado de organizaciones que el usuario esta vinculado es necesario que seleccione una.
*  *Paso 3*: Al seleccionar una organizacion es necesario dar click en uno de los siguientes botones que dan acceso a diversos modulos.

Luego de cumplir con los pasos anteriores en la barra del costado izquierdo se habilitaran mas opciones, por consiguiente se debera dar click a las siguientes opciones:
**Reportes informes y Procedimientos**.

.. image:: ../_static/procedure/images/steps_to_view_procedure_templates.png
    :width: 700
    :height: 400

Explicacion de pasos:

*  *Paso 1*: Es dar click en la opción *Reportes informes y Procedimientos* de la barra lateral izquierda, esto para habilitar los modulos de informes.
*  *Paso 2*: En este paso se da click en la opción *Plantillas de Procedimientos*, para acceder al modulo de plantillas de procedimiento.

    .. note::
        El usuario debe tener el permiso *view_procedure* para que esta opción sea visible en la barra lateral.


Permisos requeridos:

* *view_procedure*: Permite visualizar el item  y listado de **"Plantillas de procedimientos"**.
* *add_procedure*: Autoriza el ingreso a la vista de **"Creación de plantillas de procedimientos"**.
* *change_procedure*: Autoriza el ingreso a la vista de **"Actualización de plantillas de procedimientos"**.
* *delete_procedure*: Autoriza eliminar una plantilla de procedimiento.
* *view_procedurestep*: Permite visualizar el listado pasos necesarios para la elaboración del procedimiento.
* *add_procedurestep*: Autoriza el ingreso a la vista de **"Creación de pasos del procedimiento"**.

Crear plantilla de procedimientos
**********************************

academic/<int:org>/procedure/procedure_create/

Cuando se menciona una plantilla de procedimientos, se hace referencia a la platilla utilizada para la
elaboración de procedimientos químicos dentro la organización asociada, por lo tanto todos los laboratorios
vinculados a esta tendrán acceso.

Datos Requeridos:

*   *Título*: Este campo registrara el título de la plantilla.
*   *Descripción*: Este campo registrara la descripción del procedimiento, ademas se puede manipular el texto
    ya que el viene integrado con un editor de texto, permitiendo ingresar tipografías, alineación de texto, tablas,
    imagenes entre otras mas funcionalidades que trae consigo un editor de texto.

Permisos requeridos:

* *view_procedure*: Permite visualizar el item  y listado de **"Plantillas de procedimientos"**.
* *add_procedure*: Autoriza el ingreso a la vista de **"Creación de plantillas de procedimientos"**.
* *change_procedure*: Autoriza el ingreso a la vista de **"Actualización de plantillas de procedimientos"**.

Ejemplo de creación de plantilla de procedimiento:

.. image:: ../_static/gif/create_procedure_template.gif


Actualizar plantilla de procedimientos
****************************************

academic/<int:org>/procedure/procedure_update/<int:pk>/

En la actualización de plantillas funciona de forma similar que la creación de estas el unico detalle a tener en cuenta,
es que al modificar algunos de sus datos afecta a los procedimientos que se encuentren en el momento utilizando la plantilla
de procedimientos en el modulos **"Mis procedimientos"**.

Datos Requeridos:

*   *Título*: Este campo registrara el título de la plantilla.
*   *Descripción*: Este campo registrara la descripción del procedimiento, ademas se puede manipular el texto
    ya que el viene integrado con un editor de texto, permitiendo ingresar tipografías, alineación de texto, tablas,
    imágenes entre otras mas funcionalidades que trae consigo un editor de texto.

Permisos requeridos:

* *view_procedure*: Permite visualizar el item  y listado de **"Plantillas de procedimientos"**.
* *add_procedure*: Autoriza el ingreso a la vista de **"Creación de plantillas de procedimientos"**.
* *change_procedure*: Autoriza el ingreso a la vista de **"Actualización de plantillas de procedimientos"**.


Ejemplo de actualizacion de plantilla de procedimiento:

.. image:: ../_static/gif/update_procedure_template.gif


Visualizar plantilla de procedimientos
****************************************

academic/<int:org>/procedure/procedure_detail/<int:pk>/

En esta vista se visualizará la plantilla de procedimiento seleccionada, la cual mostrará la informacion ingresada,
además de sus pasos con sus objectos y observaciones para la ejecución del procedimiento quimico.

Permisos requeridos:

* *view_procedure*: Permite visualizar el item  y listado de **"Plantillas de procedimientos"**.
* *change_procedure*: Autoriza el ingreso a la vista de **"Actualización de plantillas de procedimientos"**.
* *delete_procedurestep*: Permite visualizar el boton de **"Eliminar Paso de plantilla"**.


Agregar pasos
**************

academic/<int:org>/procedure/add_steps_wrapper/<int:pk>/

Cuando se mencionan pasos en una plantilla de procedimientos, se hace referencia a las indicaciones requeridadas
a la hora de generar un procedimiento químico, este paso se genera por defecto dando click en el botón con el símbolo
**+** en la listas de plantillas de procedimientos.

Datos requeridos:

*   *Título*: Este campo registrara el título de la plantilla, si no se ingresa ningún palabra este título se mostrará,
    en la visualización de plantillas de procedimientos como **"Desconocido"**.
*   *Descripción*: Este campo registrara la descripción del procedimiento, además se puede manipular el texto
    ya que el viene integrado con un editor de texto, permitiendo ingresar tipografías, alineación de texto, tablas,
    imágenes entre otras mas funcionalidades que trae consigo un editor de texto.

Permisos Requeridos:

*   *add_procedurestep*: Autoriza ingresar a la vista de **Crear Paso**.

**Ejemplo de agregar un paso de una plantilla de procedimiento**:

.. image:: ../_static/gif/add_step.gif



Actualizar pasos
*****************

academic/<int:org>/procedure/step/<int:pk>/update/

En la actualización de pasos trabaja de forma similar que la actualización de plantillas de procedimientos con los mismos
campos.

Datos requeridos:

*   *Título*: Este campo registrara el título de la plantilla, si no se ingresa ningún palabra este título se mostrará, en la visualización de plantillas de procedimientos como **"Desconocido"**.
*   **Descripción**: Este campo registrara la descripción del procedimiento, además se puede manipular el texto
    ya que el viene integrado con un editor de texto, permitiendo ingresar tipografías, alineación de texto, tablas,
    imágenes entre otras mas funcionalidades que trae consigo un editor de texto.

Permisos Requeridos:

*   *add_procedurestep*: Autoriza ingresar a la vista de **Crear Paso**.

**Ejemplo de actualizar un paso de una plantilla de procedimiento**:

.. image:: ../_static/gif/update_step.gif


Agregar objectos en los pasos
*******************************

academic/<int:org>/procedure/save_object/<int:pk/

Cuando hablamos de objectos dentro los pasos son el listado de materiales utilizados en los procedimientos, los cuales
serán reservados para más información de este revisar la viñeta **Generar Reservación de Procedimiento**.

Datos requeridos:

*   *Objecto*: Este campo es un selector con un listado de objectos vinculados a la organización, es obligatorio
    escoger una opción.
*   *Cantidad*: Este campo anota la cantidad a utilizar del material u objecto utilizar en el procedimiento, además
    la cantidad mínima a ingresar debe ser de **0.0000001** si esta cantidad es inferior al mínimo sobre este campo
    aparece el mensaje.

    .. warning::
        **Asegúrese de que este valor es mayor o igual a 1e-07**.

*   *Unidad de medida*: Este campo hace referencia a la unidad de medida del objecto seleccionado, a su vez es
    obligatoria la selección de una opción.

Permisos requeridos:

*   *add_procedurerequiredobject*: Permite agregar objectos a los pasos de la plantilla de procedimientos.

**Ejemplo de agregar de objecto**:

.. image:: ../_static/gif/add_step_object.gif


Descartar objecto
*******************

academic/<int:org>/procedure/remove_object/<int:pk/

Al descartar un objecto de un viene siendo, igual que eliminarlo, pero de un paso no estamos hablando de borrarlo del
sistema en sí, hay un detalle que se debe tomar en cuenta a la hora de eliminar y es que afecta procedimientos que este
relacionado a la plantilla.

Permisos requeridos:

*   *delete_procedurerequiredobject*: Permite eliminar un objecto de los pasos de la plantilla de procedimientos.

**Ejemplo de descarte de objecto**:

.. image:: ../_static/gif/remove_step_object.gif



Agregar observación
*********************

academic/<int:org>/procedure/add_observation/<int:pk>/

Las observaciones son las indicaciones preventivas para manipulación de los objectos.

Datos requeridos:

*   *Descripción*: En este campo se ingresara el detalle de la observación.

Permisos requeridos:

*   *add_procedureobservations*: Autoriza el agregar observaciones en los pasos.

**Ejemplo de creación de observación**:

.. image:: ../_static/gif/add_observation.gif



Eliminar observación
***********************

academic/<int:org>/procedure/remove_observation/<int:pk>/

Al dar click en icono eliminar de la observación seleccionada se mostrará la siguiente ventana.

.. image:: ../_static/procedure/observations/images/remove_template_procedure_observation.jpg
  :width: 700
  :height: 400

.. note::
    Si se presiona la opción **Si**, se elimina la observación, pero si presiona la opción **No**, no se elimina la observación.

Permisos Requeridos:

*   *delete_procedureobservations*: Autoriza el agregar observaciones en los pasos.


Ejemplo de eliminación de observación:

.. image:: ../_static/gif/remove_observation.gif


Eliminar paso
***************

academic/<int:org>/procedure/step/delete/

Para eliminar un paso de una plantilla plantilla de procedimientos se debe tener en cuenta varios aspectos:

*   Al eliminar un paso se borran todos los objectos que poseen que por consecuencia afectaría procedimientos que esten,
    utiliza esta.
*   También se eliminaran las obsevaciones.

Permisos Requeridos:

* *change_procedure*: Autoriza el ingreso a la vista de **"Actualizacion de plantillas de procedimientos"**.
* *delete_procedure*: Autoriza eliminar una plantilla de procedimiento.
* *view_procedurestep*: Permite visualizar el listado pasos necesarios para la elaboración del procedimiento.
* *delete_procedurestep*: Permite visualizar el botón de eliminar paso en la vista **"Actualización de plantillas de procedimientos"**
    y autoriza su eliminación.

.. important::
    **Nota**: Hay que tener en cuenta a la hora de modificar o eliminar un **Paso** este también afecta a los procedimientos,
    que anteriormente han utilizado la plantilla, esto provocando cambios en la generación de reservas de materiales,
    de procedimientos que usa esta plantilla de referencia.


Eliminar plantilla de procedimientos
***************************************

academic/<int:org>/procedure/delete_procedure/

Para eliminar una plantilla plantilla de procedimientos se debe tener en cuenta varios aspectos:

*   Los procedimientos vinculados a esta plantilla en consecuencia a la eliminación terminaran sin plantilla, por lo tanto se recomienda cambiar la plantilla del procedimiento.
*   También se van a eliminar los pasos y observaciones.
*   No solo las plantillas de la organización seran afectadas sino que las organizaciones hijas se verán influenciadas.

**Ejemplo de eliminación de plantilla**:

.. image:: ../_static/gif/delete_procedure_template.gif


Permisos Requeridos:

* *delete_procedure*: Autoriza eliminar una plantilla de procedimiento.
* *view_procedure*: Permite visualizar las lista de plantillas de procedimientos de la organización.


Administrar mis procedimientos
---------------------------------

academic/<int:org>/myprocedure/<int:lab_pk>/get_list/


Crear procedimiento
********************

add_procedures/<str:content_type>/<str:model>/

Actualizar procedimientos
***************************************

academic/<int:org>/myprocedure/<int:lab_pk>/complete_procedure/<int:pk>/

Visualizar comentarios de procedimiento
****************************************

spc/api/<int:org>/<int:lab_pk>/api_procedure_comments

Agregar comentario en procedimiento
***************************************

/spc/api/<int:org>/<int:lab_pk>/api_my_procedure/add_comment/

Actualizar comentario de procedimiento
***************************************

/spc/api/<int:org>/<int:lab_pk>/api_my_procedure/<int:pk>/update_comment/

Eliminar comentario de procedimiento.
**************************************
/spc/api/<int:org>/<int:lab_pk>/api_my_procedure/<int:pk>/delete_comment/

Generar Reservas
*******************

Eliminar procedimiento
**************************
