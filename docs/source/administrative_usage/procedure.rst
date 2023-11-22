Administrar plantillas de procedimientos
***************************************

/academic/<int:org>/procedure/procedure_list/

* **"view_procedure"**: Permite visualizar el item  y listado de **"Plantillas de procedimientos"**.

* **"add_procedure"**: Autoriza el ingreso a la vista de **"Creacion de plantillas de procedimientos"**.

* **"change_procedure"**: Autoriza el ingreso a la vista de **"Actualizacion de plantillas de procedimiento"s**.

* **"delete_procedure"**: Autoriza eliminar una plantilla de procedimiento.

* **"view_procedurestep"**: Permite visualizar el listado pasos necesarios para la elaboración del procedimiento.

* **"add_procedurestep"**: Autoriza el ingreso a la vista de **"Creación de pasos del procedimiento"**.


Crear plantilla de procedimientos
=================
academic/<int:org>/procedure/procedure_create/

Cuando se menciona una plantilla de procedimientos, se hace referencia a la platilla utilizada para la
elaboracion de procedimientos quimicos dentro la organizacion asociada por lo tanto todos los laboratorios
vinculados a esta tendrán acceso.

Datos Requeridos:

*   **Titulo**: Este campo registrara el titulo de la plantilla.

*   **Descripcion**: Este campo registrara la descripcion del procedimiento, ademas se puede manipular el texto
ya que el viene integrado con un editor de texto, permitiendo ingresar tipografías, alineacion de texto, tablas,
imagenes entre otras mas funcionalidades que trae consigo un editor de texto.

Permisos requeridos:

* **"view_procedure"**: Permite visualizar el item  y listado de **"Plantillas de procedimientos"**.

* **"add_procedure"**: Autoriza el ingreso a la vista de **"Creacion de plantillas de procedimientos"**.

* **"change_procedure"**: Autoriza el ingreso a la vista de **"Actualizacion de plantillas de procedimiento"s**.


Actualizar plantilla de procedimientos
=================

academic/<int:org>/procedure/procedure_update/<int:pk>/

En la actualización de plantillas funciona de forma similar que la creacion de estas el unico detalle a tener en cuenta,
es que al modificar algunos de sus datos afecta a los procedimientos que se encuentren en el momento utilizando la plantilla
de procedimientos en el modulos **"Mis procedimientos"**.

Datos Requeridos:

*   **Titulo**: Este campo registrara el titulo de la plantilla.

*   **Descripcion**: Este campo registrara la descripcion del procedimiento, ademas se puede manipular el texto
ya que el viene integrado con un editor de texto, permitiendo ingresar tipografías, alineacion de texto, tablas,
imagenes entre otras mas funcionalidades que trae consigo un editor de texto.

Permisos requeridos:

* **"view_procedure"**: Permite visualizar el item  y listado de **"Plantillas de procedimientos"**.

* **"add_procedure"**: Autoriza el ingreso a la vista de **"Creacion de plantillas de procedimientos"**.

* **"change_procedure"**: Autoriza el ingreso a la vista de **"Actualizacion de plantillas de procedimiento"s**.

Visualizar plantilla de procedimientos
=================

academic/<int:org>/procedure/procedure_detail/<int:pk>/

En esta vista se visualizara la plantilla de procedimiento seleccionada, la cual mostrara la informacion ingresada,
ademas de sus pasos con sus objectos y observaciones para la ejecucion del procedimiento quimico.

Permisos requeridos:

* **"view_procedure"**: Permite visualizar el item  y listado de **"Plantillas de procedimientos"**.

* **"change_procedure"**: Autoriza el ingreso a la vista de **"Actualizacion de plantillas de procedimientos"**.

* **"delete_procedurestep"**: Permite visualizar el boton de **"Eliminar Paso de plantilla"**.


Agregar pasos
=================

academic/<int:org>/procedure/add_steps_wrapper/<int:pk>/

Cuando se mencionan pasos en una plantilla de procedimientos, se hace referencia a las indicaciones requeridadas
a la hora de generar un procedimiento quimico, este paso se genera por defecto dando click en el boton con el simbolo
**+** en la listas de plantillas de procedimientos.
Datos requeridos:
*   **Titulo**: Este campo registrara el titulo de la plantilla, si no se ingresa ningun palabra este titulo se mostrara,
en la visualizacion de plantillas de procedimientos como **"Desconocido"**.

*   **Descripcion**: Este campo registrara la descripcion del procedimiento, ademas se puede manipular el texto
ya que el viene integrado con un editor de texto, permitiendo ingresar tipografías, alineacion de texto, tablas,
imagenes entre otras mas funcionalidades que trae consigo un editor de texto.

Permisos Requeridos:
*   **"add_procedurestep"**: Autoriza ingresar a la vista de "Crear Paso" y crear pasos.

Actualizar pasos
=================

academic/<int:org>/procedure/step/<int:pk>/update/

En la actualizacion de pasos trabaja de forma similar que la actualizacion de plantillas de procedimientos con los mismos
campos.
Datos requeridos:
*   **Titulo**: Este campo registrara el titulo de la plantilla, si no se ingresa ningun palabra este titulo se mostrara,
en la visualizacion de plantillas de procedimientos como **"Desconocido"**.

*   **Descripcion**: Este campo registrara la descripcion del procedimiento, ademas se puede manipular el texto
ya que el viene integrado con un editor de texto, permitiendo ingresar tipografías, alineacion de texto, tablas,
imagenes entre otras mas funcionalidades que trae consigo un editor de texto.

Tambien hay que tener en cuenta a la hora de modificar los datos del **Paso** este tambien afecta a los procedimientos,
que anteriormente han utilizado la plantilla, esto provocando cambios en la generacion de reservas, un paso, contiene
los materiales utilizados para el procedimientos ademas de observaciones para el uso de estos.
Permisos Requeridos:
*   **"add_procedurestep"**: Autoriza ingresar a la vista de "Crear Paso" y crear pasos.


Agregar objectos en los pasos
=================

academic/<int:org>/procedure/save_object/<int:pk/

Cuando hablamos de objectos dentro los pasos son el listado de materiales utilizados en los procedimientos, los cuales
seran reservados para mas informacion de este revisar la viñeta **Generar Reservacion de Procedimiento**.

Datos requeridos:

*   **Objecto**: Este campo es un selector con un listado de objectos vinculados a la organización, es obligatorio
escoger una opción.

*   **Cantidad**: Este campo anota la cantidad a utilizar del material u objecto utilizar en el procedimiento, ademas
la cantidad minima a ingresar debe ser de **0.0000001**.

*   **Unidad de medida**: Este campo hace referencia a la unidad de medida del objecto seleccionado, a su vez es
obligatoria la seleccion de una opcion.

Permisos requeridos:

*   **"add_procedurerequiredobject"**: Permite agregar objectos a los pasos de la plantilla de procedimientos.


Descartar objecto
=================

academic/<int:org>/procedure/remove_object/<int:pk/

El descartar un objecto de un viene siendo, igual que eliminarlo pero de un paso no estamos hablando de borralo del
sistema en sí, hay detalle en tomar en cuenta a la hora de eliminar

Datos requeridos:

*   **Pk**: Este dato representa el **id** del objecto que se desea descartar por lo tanto sino posee este dato mostrara,
siguientes imagen.



Permisos requeridos:

*   **"delete_procedurerequiredobject"**: Permite eliminar un objecto de los pasos de la plantilla de procedimientos.



Agregar observacion
=================

academic/<int:org>/procedure/add_observation/<int:pk>/

Eliminar observacion
=================

academic/<int:org>/procedure/remove_observation/<int:pk>/

Eliminar paso
=================

academic/<int:org>/procedure/step/delete/

Eliminar plantilla de procedimientos
===========================

academic/<int:org>/procedure/delete_procedure/


explicar las consecuencias de eliminar un procedimiento.
