# Inventario de funcionalidades

Generado por `make feature-catalog`. No editar a mano: se regenera.

Una **funcionalidad** es una acción de usuario de varios pasos, no una ruta.
Cada paso declara **qué rol lo ejecuta**, que es lo único de este catálogo
que no se puede deducir del código — y justamente lo que hacía falta para
poder decir qué roles no están probados.

La columna de cobertura sale de `annotate_coverage()` y es **una pista, no
una medición**: dice que alguna prueba nombra esa ruta, no que la ejercite
con ese rol.

## Resumen

| Métrica | Valor |
|---|---:|
| Funcionalidades catalogadas | 44 |
| Sin ninguna prueba | 11 |
| Rutas navegables huérfanas | 0 |
| Apps pendientes de catalogar | 2 |
| Roles canónicos | 18 |
| Roles canónicos sin aparecer en ningún paso | 0 |

## Funcionalidades

### `ACAD-01` — Diseñar una plantilla de procedimiento con sus pasos

*academic · ui · prioridad P2 · cobertura por ruta: completa · Selenium: sí*

El docente crea la plantilla de una práctica, le añade pasos ordenados y declara qué objetos del inventario requiere cada uno. Es lo que después se instancia para cada grupo y lo que dispara la reserva del material.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Crear la plantilla del procedimiento** | Profesor, Administrador de Laboratorio, Asistente de laboratorio | `academic.add_procedure` | — | `academic:procedure_create` |
| **Listar y consultar plantillas** | Profesor, Administrador de Laboratorio, Asistente de laboratorio, Estudiante, Solo Lectura | `academic.view_procedure` | — | `academic:procedure_list`<br>`academic:procedure_detail`<br>`academic:get_procedure` |
| **Editar la plantilla** | Profesor, Administrador de Laboratorio, Asistente de laboratorio | `academic.change_procedure` | — | `academic:procedure_update` |
| **Añadir pasos a la plantilla** | Profesor, Administrador de Laboratorio, Asistente de laboratorio | `academic.add_procedurestep` | — | `academic:procedure_step`<br>`academic:add_steps_wrapper` |
| **Editar un paso** | Profesor, Administrador de Laboratorio, Asistente de laboratorio | `academic.change_procedurestep` | — | `academic:update_step` |
| **Borrar un paso o la plantilla completa** | Profesor, Administrador de Laboratorio, Asistente de laboratorio | `academic.delete_procedurestep`<br>`academic.delete_procedure` | — | `academic:delete_step`<br>`academic:delete_procedure` |

### `ACAD-02` — Ejecutar un procedimiento y reservar el material que necesita

*academic · ui · prioridad P2 · cobertura por ruta: completa · Selenium: sí*

A partir de una plantilla se crea «mi procedimiento» para un laboratorio concreto, se genera de golpe la reserva de todo el material que los pasos requieren, y se va completando hasta darlo por finalizado.

Estados que atraviesa:

- `MyProcedure.status: "Eraser" → "In Review" → "Finalized" (`academic/models.py:33-37`)`

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Crear mi procedimiento a partir de una plantilla** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | `academic.add_myprocedure` | → MyProcedure.status="Eraser" | `academic:add_my_procedures` |
| **Ver mis procedimientos** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | `academic.view_myprocedure` | — | `academic:get_my_procedures` |
| **Generar la reserva de todo el material del procedimiento** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | `reservations_management.add_reservedproducts` | crea Reservations(is_massive=True) — entra en RES-01 | `academic:generate_reservation` |
| **Completar los pasos y cambiar el estado** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | `academic.change_myprocedure` | "Eraser" → "In Review" → "Finalized", según el POST | `academic:complete_my_procedure` |
| **Quitar mi procedimiento** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | `academic.delete_myprocedure` | — | `academic:remove_my_procedure` |

Hallazgos:

- HALLAZGO-ACAD-1: **no hay rol revisor.** `MyProcedure` declara los tres estados de un flujo de revisión, pero `complete_my_procedure` (`views.py:253`) toma el `status` directamente del POST bajo el mismo `change_myprocedure` que sirve para editarlo. Quien ejecuta el procedimiento se lo aprueba a sí mismo: el estado «In Review» no tiene quien lo revise. Compárese con `laboratory.Inform` (`laboratory/models.py:1643-1674`), que tiene los mismos tres estados **y sí** un permiso de aprobación aparte (`laboratory.can_manage_inform_status`).
- La reserva masiva nace aquí pero se aprueba y se cierra en RES-01: es el único flujo del sistema que cruza dos módulos con actores distintos.

### `ORG-01` — Elegir organización y orientarse en el árbol

*auth_and_perms · ui · prioridad P1 · cobertura por ruta: parcial · Selenium: sí*

La puerta de entrada del sistema multiinquilino: el usuario elige en qué organización trabaja, y a partir de ahí todo lleva `org_pk` en la URL. También el mapa de laboratorios y el listado de organizaciones y sus labs.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Elegir la organización con la que se trabaja** | Estudiante, Profesor, Técnico de Laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — | — | `auth_and_perms:select_organization_by_user` |
| **Ver el mapa de laboratorios** | Administrador de Laboratorio, Administrativo superior, Regente | `risk_management.view_riskzone` | — | `auth_and_perms:map_of_laboratories` |
| **Listar organizaciones y sus laboratorios** | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | `laboratory.view_organizationstructure` | — | `auth_and_perms:lab_org_list` |

Hallazgos:

- El mapa de laboratorios exige `risk_management.view_riskzone`: para ver dónde están los laboratorios hace falta un permiso del módulo de riesgo.

### `ORG-02` — Administrar la organización: usuarios, roles y estructura

*auth_and_perms · ui · prioridad P1 · cobertura por ruta: parcial · Selenium: sí*

La pantalla desde la que un administrador arma su inquilino: da de alta usuarios, crea y edita roles, copia el juego de roles a otra organización, habilita las organizaciones hijas y relaciona modelos con la organización. Es donde se materializa el eje de roles que este catálogo usa.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Abrir el gestor de la organización** | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | `laboratory.can_manage_org_permissions` | — | `auth_and_perms:organizationManager` |
| **Añadir usuarios a la organización** | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | `auth.add_user`<br>`laboratory.change_organizationstructure`<br>`auth_and_perms.view_profile` | — | `auth_and_perms:add_user`<br>`auth_and_perms:addusersorganization`<br>`auth_and_perms:get_users` |
| **Consultar, crear y editar los roles de la organización** | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | `auth_and_perms.change_rol`<br>`auth_and_perms.view_rol` | — | `auth_and_perms:list_rol_by_org`<br>`auth_and_perms:update_rol`<br>`auth_and_perms:get_rol`<br>`auth_and_perms:get_roles_by_organization`<br>`auth_and_perms:add_rol_by_laboratory` |
| **Quitar un rol de la organización** | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | `auth_and_perms.delete_rol` | — | `auth_and_perms:del_rol_by_org` |
| **Copiar el juego de roles a otra organización** | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | `laboratory.change_organizationstructure` | — | `auth_and_perms:copy_rols` |
| **Habilitar organizaciones hijas y relacionar modelos** | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | `laboratory.change_organizationstructure` | — | `auth_and_perms:enable_child_organizations`<br>`auth_and_perms:add_contenttype_to_org` |
| **Consultar quién administra la organización** | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | — | — | `auth_and_perms:get_org_administrators` |

Hallazgos:

- HALLAZGO-ORG-1: `get_org_administrators` (`:542`) filtra por `rol__name="Administrativo superior"`, una **cadena literal**. Renombrar ese rol deja la consulta vacía sin que nada falle.
- Listar roles exige `change_rol`, no `view_rol`: no se puede dar consulta de roles sin dar edición.

### `ORG-03` — Entrar con firma digital o segundo factor

*auth_and_perms · ui · prioridad P3 · cobertura por ruta: **sin prueba** · Selenium: —*

El acceso por firma digital del BCCR —el usuario se crea si no existe— y el código QR del segundo factor TOTP.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Autenticarse con la firma digital del BCCR** | Anónimo | — | — | `auth_and_perms:login_with_bccr`<br>`auth_and_perms:check_signature_window_status_register` |
| **Obtener el QR del segundo factor** | Estudiante, Profesor, Administrador de Laboratorio | — | — | `auth_and_perms:show_qr_img` |

Hallazgos:

- `login_with_bccr` está excluida del smoke a propósito (`url_smoke.py` `SMOKE_EXCLUDES`): abre la ventana de firma digital.

### `ORG-04` — Suplantar a otro usuario para dar soporte

*auth_and_perms · ui · prioridad P1 · cobertura por ruta: **sin prueba** · Selenium: —*

Quien tiene el permiso entra en la sesión de otro usuario de su misma organización para reproducir lo que ese usuario ve, y luego sale. Queda registrado en `ImpostorLog` con IP y token.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Entrar como otro usuario** | Administrativo superior, Organization Management | `auth_and_perms.change_impostorlog` | crea ImpostorLog(logged_in) y la cookie impostor_token | `auth_and_perms:change_to_impostor` |
| **Volver a la identidad propia** | Administrativo superior, Organization Management | — | cierra el ImpostorLog | `auth_and_perms:remove_impostor` |

Hallazgos:

- HALLAZGO-ORG-2: **no hay restricción de privilegio.** Las cuatro guardas (`impostor.py:19-63`) comprueban que el suplantado pertenezca a la misma organización, que no sea uno mismo y que no haya otra sesión activa — pero no que el suplantador tenga al menos tantos permisos como el suplantado. Quien tenga `change_impostorlog` puede entrar como el administrador de su organización. Es una escalada de privilegios por diseño, y la auditoría en `ImpostorLog` es el único control.
- Las dos rutas están fuera del smoke porque rompen la sesión de la corrida; necesitan prueba propia.

### `INV-01` — Mantener el catálogo de objetos: reactivos, materiales y equipos

*laboratory · ui · prioridad P1 · cobertura por ruta: parcial · Selenium: sí*

La ficha maestra de cada cosa que puede haber en el laboratorio, con sus características y sus rasgos. Los tres listados —sustancias, materiales y equipos— son la misma pantalla filtrada por el tipo de objeto.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Listar sustancias, materiales y equipos** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | `laboratory.view_object` | — | `laboratory:sustance_list`<br>`laboratory:equipment_list`<br>`laboratory:object_view` |
| **Dar de alta un objeto en el catálogo** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | `laboratory.add_object` | — | `laboratory:objectview_create` |
| **Editar o borrar un objeto del catálogo** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | `laboratory.change_object`<br>`laboratory.delete_object` | — | `laboratory:objectview_update`<br>`laboratory:objectview_delete` |
| **Consultar los rasgos de los objetos** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | `laboratory.view_objectfeatures` | — | `laboratory:objectfeatures_view` |
| **Consultar los proveedores** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | `laboratory.view_provider` | — | `laboratory:provider_view` |

### `INV-02` — Operar un objeto en el estante: crear, aumentar, disminuir, mover y desechar

*laboratory · ui · prioridad P1 · cobertura por ruta: parcial · Selenium: sí*

El trabajo diario: poner una caja de reactivo en un estante, consumir parte, reponer, moverla a otro estante, consultar su detalle con su QR y su bitácora, y al final desecharla. Todo pasa por modales sobre la vista del laboratorio.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Ver los objetos de un estante** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — | — | `laboratory:list_shelfobject` |
| **Colocar un objeto en el estante** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Depositante de residuos | `laboratory.add_shelfobject` | — | `laboratory:shelfobject_create` |
| **Abrir el detalle del objeto, con su QR** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | `laboratory.view_shelfobject` | — | `laboratory:shelfobject_detail`<br>`laboratory:download_shelfobject_qr`<br>`laboratory:equipment_shelfobject_detail` |
| **Editar la cantidad, el límite y los datos del objeto** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante | `laboratory.change_shelfobject` | — | `laboratory:shelfobject_edit`<br>`laboratory:shelfobject_searchupdate`<br>`laboratory:get_shelfobject_limit`<br>`laboratory:shelf_object_hcode` |
| **Generar la etiqueta del objeto** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — | — | `laboratory:generate_shelfobject_label`<br>`laboratory:shelfobject_label` |
| **Borrar o desechar el objeto** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Depositante de residuos, Tesista modulo desechos | `laboratory.delete_shelfobject` | — | `laboratory:shelfobject_delete`<br>`laboratory:disposal_substance` |
| **Ver los reactivos del estante y su reorden** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | `laboratory.can_manage_reorder` | — | `laboratory:shel_objects_reactives` |

Hallazgos:

- La regla de descarte cambia el permiso según el estante: si el estante es de descarte, borrar exige `can_manage_disposal` en vez de `delete_shelfobject`. Depende del contenedor, no del objeto — es el único permiso del sistema que se decide por el sitio.

### `INV-03` — Cargar inventario en masa desde un fichero

*laboratory · ui · prioridad P2 · cobertura por ruta: **sin prueba** · Selenium: —*

La alternativa a dar de alta reactivo por reactivo: se sube un fichero, se revisa lo que se va a crear y se confirma. Es la vía de entrada de un laboratorio que empieza.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Subir el fichero y previsualizar** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | `laboratory.add_shelfobject` | — | `laboratory:load_archive` |
| **Confirmar y crear los objetos en el estante** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | `laboratory.add_shelfobject` | — | `laboratory:load_archive_create_shelfobjects` |

### `INV-04` — Vigilar existencias, vencimientos y límites

*laboratory · ui · prioridad P2 · cobertura por ruta: **sin prueba** · Selenium: sí*

El panel de existencias de reactivos, los avisos cuando algo baja del límite o está por vencer, y la posibilidad de silenciarlos. Buena parte del trabajo lo hace el planificador, no una persona.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Ver el panel de existencias de reactivos** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Regente | `laboratory.view_laboratory` | — | `laboratory:reactive_stock_list` |
| **Silenciar los avisos de un objeto** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | — | — | `laboratory:block_notification` |

### `INV-05` — Vigilar el inventario automáticamente y avisar

*laboratory · celery · prioridad P2 · cobertura por ruta: **sin prueba** · Selenium: —*

Las cinco tareas programadas del inventario: avisar cuando un producto baja de su límite, registrar el máximo diario, avisar de los vencimientos, preparar el reporte mensual de precursores y limpiar las relaciones huérfanas entre organización y laboratorio. Ninguna tiene pantalla; todas crean tareas pendientes o mandan correo.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Avisar de los productos que llegaron a su límite** | Sistema | — | crea PendingTask para los responsables del laboratorio | — |
| **Registrar el stock máximo del día** | Sistema | — | — | — |
| **Avisar por correo de los objetos por vencer** | Sistema | — | — | — |
| **Preparar el reporte mensual de precursores** | Sistema | — | — | — |
| **Limpiar las relaciones huérfanas organización-laboratorio** | Sistema | — | — | — |

### `INV-06` — Redactar y aprobar informes periódicos

*laboratory · ui · prioridad P2 · cobertura por ruta: completa · Selenium: sí*

Los informes del laboratorio, con su agendador de periodos: se programa cada cuánto toca, alguien lo completa y **alguien distinto** cambia su estado. Es el único flujo del módulo con un permiso de aprobación propio.

Estados que atraviesa:

- `Inform.status: "Eraser" → "In Review" → "Finalized" (`laboratory/models.py:1643-1674`)`

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Programar el periodo de los informes** | Administrador de Laboratorio, Asistente de laboratorio | `laboratory.add_informscheduler`<br>`laboratory.change_informscheduler`<br>`laboratory.view_informscheduler`<br>`laboratory.view_inform` | — | `laboratory:add_period_scheduler`<br>`laboratory:edit_period_scheduler`<br>`laboratory:detail_period_scheduler`<br>`laboratory:inform_index` |
| **Crear el informe** | Administrador de Laboratorio, Asistente de laboratorio, Técnico de Laboratorio | `laboratory.add_inform`<br>`laboratory.view_inform` | → status="Eraser" | `laboratory:add_informs`<br>`laboratory:get_informs` |
| **Completar el informe y cambiar su estado** | Administrador de Laboratorio | `laboratory.change_inform` | "Eraser" → "In Review" → "Finalized" | `laboratory:complete_inform` |
| **Retirar un informe** | Administrador de Laboratorio | `laboratory.delete_inform` | — | `laboratory:remove_inform` |

Hallazgos:

- El cambio de estado se protege con `laboratory.can_manage_inform_status` (`models.py:1674`) y se comprueba en la plantilla (`complete_inform.html:25`). Es el contraejemplo de HALLAZGO-ACAD-1: los mismos tres estados que `MyProcedure`, pero aquí el paso de aprobación sí tiene permiso propio.
- HALLAZGO-INV-1: **el repositorio no dice quién tiene ese permiso.** `update_roles.py` solo lo menciona en `:100`, dentro del `remove_permissions` de «Depositante de residuos» — es decir, dice quién *no* lo tiene. El conjunto de permisos de cada rol canónico no está versionado en ninguna parte: `update_roles.py` aplica deltas sobre roles que supone existentes (`filter(...).first()` → «not found, skipping») y `upload_org_and_users.py:45` hace `Rol.objects.get(...)`, que en una instalación limpia revienta. La definición vive solo en las bases de producción.

### `INV-07` — Consultar los reportes de inventario del laboratorio

*laboratory · ui · prioridad P2 · cobertura por ruta: parcial · Selenium: sí*

Los reportes que viven en el propio módulo de laboratorio, antes de pasar por el ciclo asíncrono de `report`: inventario químico, códigos H, presencia de reactivos en la organización y cobertura de fichas.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Abrir el índice de reportes del laboratorio** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | `laboratory.view_report` | — | `laboratory:reports`<br>`laboratory:chemicalinventory`<br>`laboratory:organizationreactivepresence` |
| **Consultar y descargar los reportes de códigos H** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | `laboratory.do_report` | — | `laboratory:h_code_reports`<br>`laboratory:download_h_code_reports` |
| **Descargar el reporte de objetos en estantes** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | `laboratory.do_report` | — | `laboratory:reports_shelf_objects` |
| **Ver la cobertura de fichas de seguridad** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — | — | `laboratory:sds_coverage_svg` |

### `INV-08` — Documentar protocolos del laboratorio

*laboratory · ui · prioridad P3 · cobertura por ruta: completa · Selenium: sí*

Los protocolos que el laboratorio documenta y adjunta. Usan borrado lógico: al eliminarlos van a la papelera de LAB-07.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Listar protocolos** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | `laboratory.view_protocol` | — | `laboratory:protocol_list` |
| **Crear o editar un protocolo** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | `laboratory.add_protocol`<br>`laboratory.change_protocol` | — | `laboratory:protocol_create`<br>`laboratory:protocol_update` |
| **Borrar un protocolo (va a la papelera)** | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | `laboratory.delete_protocol` | — | `laboratory:protocol_delete` |

### `LAB-01` — Crear y administrar una organización

*laboratory · ui · prioridad P1 · cobertura por ruta: parcial · Selenium: —*

El inquilino: se crea la organización, se edita, se le asocian acciones y eventualmente se borra. Todo lo demás cuelga de aquí, y el `org_pk` de cada URL del sistema es esta fila.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Crear la organización** | Administrativo superior, Organization Management | `laboratory.add_organizationstructure` | — | `laboratory:create_organization` |
| **Editar la organización y sus acciones** | Administrativo superior, Organization Management | `laboratory.change_organizationstructure` | — | `laboratory:update_organization`<br>`laboratory:organization_actions` |
| **Borrar la organización** | Administrativo superior, Organization Management | `laboratory.delete_organizationstructure` | — | `laboratory:delete_organization` |

### `LAB-02` — Solicitar un laboratorio u organización y aprobarlo

*laboratory · ui · prioridad P1 · cobertura por ruta: **sin prueba** · Selenium: —*

Quien no puede crear un laboratorio lo **solicita**, y alguien con autoridad revisa la solicitud y la aprueba o la rechaza dejando una nota. Es uno de los pocos flujos del sistema con dos actores separados por un permiso propio.

Estados que atraviesa:

- `LabOrOrgRequest.status: "pending" → "approved" | "rejected" (`laboratory/models.py:1897-1908`)`

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Pedir un laboratorio nuevo o una organización nueva** | Técnico de Laboratorio, Profesor, Asistente de laboratorio, Administrador de Laboratorio | `laboratory.add_labororgrequest` | crea LabOrOrgRequest en "pending", con `requested_by` | `laboratory:lab_or_org_request_list` |
| **Revisar la solicitud y aprobarla o rechazarla** | Administrativo superior | `laboratory.can_approve_labororgrequest` | "pending" → "approved" | "rejected", con `review_notes` | `laboratory:lab_or_org_request_review` |

Hallazgos:

- **Un solo rol puede aprobar**: «Administrativo superior» (`update_roles.py:1018`, dentro de `add_permissions`). A «Administrador de Laboratorio» el mismo comando le **quita** `can_approve_labororgrequest` (`:259`, dentro de `remove_permissions`), así que quien manda en el laboratorio puede pedir pero no aprobar. Es el permiso de aprobación mejor acotado del sistema, y conviene no confundirse: `update_roles.py` aplica **deltas**, y una línea con el nombre de un permiso puede estar concediéndolo o retirándolo.
- **Ninguna de las dos rutas tiene prueba unitaria.**

### `LAB-03` — Crear un laboratorio y entrar a trabajar en él

*laboratory · ui · prioridad P1 · cobertura por ruta: parcial · Selenium: sí*

Alta y edición del laboratorio, listado de los propios, y la entrada al espacio de trabajo (`labindex`, `labview`) desde donde se opera todo lo demás.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Crear el laboratorio** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | `laboratory.add_laboratory` | — | `laboratory:create_lab` |
| **Ver mis laboratorios y entrar en uno** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | `laboratory.view_laboratory` | — | `laboratory:mylabs`<br>`laboratory:labindex`<br>`laboratory:redirect_user_to_labindex` |
| **Abrir la vista del laboratorio con su árbol de salas y estantes** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | `laboratory.view_laboratoryroom` | — | `laboratory:labview` |
| **Editar o borrar el laboratorio** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | `laboratory.change_laboratory`<br>`laboratory.delete_laboratory` | — | `laboratory:laboratory_update`<br>`laboratory:laboratory_delete` |
| **Consultar los procesos del laboratorio** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | `laboratory.view_laboratoryprocess` | — | `laboratory:laboratory_process_list` |

Hallazgos:

- El árbol del labview y sus capacidades ya tienen matriz de permisos y prueba de aislamiento entre inquilinos (`laboratory/tests/labview/test_permission_matrix.py`, `test_tenant_isolation.py`). Es el único sitio del proyecto donde eso existe, y el modelo a copiar para el resto.

### `LAB-04` — Montar salas, muebles y estantes

*laboratory · ui · prioridad P1 · cobertura por ruta: parcial · Selenium: sí*

La estructura física dentro del laboratorio: salas, los muebles que contienen y los estantes de cada mueble, con su capacidad, unidad y porcentaje de ocupación. Incluye el QR propio de cada nivel.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Listar, crear, editar y borrar salas** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | `laboratory.view_laboratoryroom`<br>`laboratory.change_laboratoryroom`<br>`laboratory.delete_laboratoryroom` | — | `laboratory:rooms_list`<br>`laboratory:rooms_create`<br>`laboratory:rooms_update`<br>`laboratory:rooms_delete` |
| **Regenerar el QR de la sala** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | `laboratory.change_laboratoryroom` | — | `laboratory:rebuild_laboratory_qr` |
| **Listar, crear, editar y borrar muebles** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | `laboratory.add_furniture`<br>`laboratory.delete_furniture` | — | `laboratory:furniture_list`<br>`laboratory:furniture_create`<br>`laboratory:furniture_update`<br>`laboratory:furniture_delete` |
| **Crear, editar y borrar estantes** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | `laboratory.add_shelf`<br>`laboratory.change_shelf`<br>`laboratory.delete_shelf` | — | `laboratory:shelf_create`<br>`laboratory:shelf_edit`<br>`laboratory:shelf_delete`<br>`laboratory:get_lab_id` |
| **Ver los contenedores de un estante** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | — | — | `laboratory:shelf_containers` |
| **Descargar el reporte de la sala** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | `laboratory.view_report` | — | `laboratory:reports_laboratory` |

### `LAB-05` — Mantener los catálogos del laboratorio

*laboratory · ui · prioridad P3 · cobertura por ruta: parcial · Selenium: —*

Los desplegables que el resto de pantallas consume: tipos de mueble, de estante, de estructura, de puesto de trabajo, estados de objeto en estante, tipos de equipo y familias instrumentales.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Dar de alta una entrada de catálogo desde el formulario** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — | — | `laboratory:add_furniture_type_catalog`<br>`laboratory:add_shelf_type_catalog`<br>`laboratory:add_structure_type_catalog`<br>`laboratory:add_workplace_type_catalog`<br>`laboratory:add_shelfobject_status` |
| **Consultar tipos de equipo y familias instrumentales** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | `laboratory.view_object`<br>`laboratory.view_catalog` | — | `laboratory:equipmenttype_list`<br>`laboratory:instrumentalfamily_list` |

Hallazgos:

- Las cinco altas de catálogo comparten vista (`add_catalog`) y **ninguna declara permiso**: cualquiera que llegue al formulario puede añadir entradas al catálogo de la organización.

### `LAB-06` — Dar de alta usuarios del laboratorio por código QR

*laboratory · ui · prioridad P2 · cobertura por ruta: parcial · Selenium: sí*

El alta rápida en el laboratorio: se genera un QR, se imprime, y quien lo escanea entra y queda registrado. Incluye su bitácora propia.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Generar y administrar los QR de registro** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | `laboratory.add_registeruserqr`<br>`laboratory.view_registeruserqr` | — | `laboratory:create_user_qr`<br>`laboratory:manage_register_user_qr`<br>`laboratory:list_register_user_qr` |
| **Descargar el PDF con el QR** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | `laboratory.view_registeruserqr` | — | `laboratory:download_register_user_qr` |
| **Escanear el QR y quedar registrado en el laboratorio** | Estudiante, Profesor, Anónimo | — | — | `laboratory:login_register_user_qr` |
| **Consultar quién entró por el QR** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — | — | `laboratory:logentry_register_user_qr` |
| **Retirar un QR de registro** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | `laboratory.delete_registeruserqr` | — | `laboratory:delete_register_user_qr` |

Hallazgos:

- `laboratory:create_user_qr` es el **único nombre duplicado** admitido en todo el proyecto: dos firmas de la misma vista, con y sin `<int:user>` (lista blanca de `test_url_inventory.py`).

### `LAB-07` — Consultar la bitácora y recuperar lo borrado

*laboratory · ui · prioridad P2 · cobertura por ruta: parcial · Selenium: —*

La trazabilidad de la organización: quién cambió qué, y la papelera desde la que se recupera lo que se borró con borrado lógico.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Consultar la bitácora de la organización** | Administrativo superior, Administrador de Laboratorio, Regente, Solo Lectura | — | — | `laboratory:logentry_list` |
| **Ver la papelera y recuperar un elemento** | Administrativo superior, Administrador de Laboratorio | `djgentelella.view_trash` | — | `laboratory:trash_list` |

Hallazgos:

- La papelera solo muestra lo que se borró pasando `related_objects=[org, lab]`: un `obj.delete()` pelado borra lógicamente pero deja el objeto invisible e irrecuperable.

### `LAB-08` — Consultar y editar el perfil propio

*laboratory · ui · prioridad P3 · cobertura por ruta: completa · Selenium: —*

Los datos de la persona: teléfono, cédula, idioma, si quiere ver los tutoriales, y el cambio de contraseña.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Ver y editar el perfil** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | `auth_and_perms.change_own_profile`<br>`auth_and_perms.view_profile` | — | `laboratory:profile`<br>`laboratory:profile_detail` |
| **Cambiar la contraseña** | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | `auth_and_perms.change_own_profile` | — | `laboratory:password_change` |

### `TASK-01` — Recibir y atender una tarea pendiente

*pending_tasks · ui · prioridad P2 · cobertura por ruta: completa · Selenium: —*

El buzón de trabajo del usuario. Otros módulos crean tareas dirigidas a una persona **o a un conjunto de roles**, y quien las recibe las ve aquí con su enlace al sitio donde se resuelven.

Estados que atraviesa:

- `PendingTask.status: PENDING(0) → IN_PROCESS(1) → FINISHED(2) (`pending_tasks/models.py:14-22`)`

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Ver mis tareas pendientes** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | `pending_tasks.view_pendingtask` | — | `pending_tasks:view_task` |

Hallazgos:

- **Es el único sitio del sistema donde el rol es dato de negocio, no solo autorización.** `PendingTask` se asigna a un `profile` *o* a un M2M de `Rol` (`models.py:32,39`), y `PendingTaskManager` resuelve destinatarios implícitos: los regentes del laboratorio (:67), su responsable (:99), los responsables de la organización (:109), los del edificio (:125), **todos los perfiles con un rol dado** (:138) y los de una organización filtrando por `type_in_organization` (:161).
- Que la app tenga una sola ruta esconde su alcance: los emisores están en `sga/utils.py:63`, `risk_management/tasks.py:67`, `risk_management/iper_views.py:575`, `laboratory/tasks.py:69,197`, `laboratory/task_utils.py:65` y `laboratory/limit_shelfobject.py:25`.

### `MSDS-01` — Consultar y verificar las fichas de seguridad del laboratorio

*msds · ui · prioridad P3 · cobertura por ruta: parcial · Selenium: sí*

El archivo de hojas de datos de seguridad: se listan las disponibles, se registra una nueva y se revisa la trazabilidad de las que el sistema ha ido extrayendo de los PDF subidos en SGA.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Consultar el árbol de fichas** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | `msds.view_msdsobject` | — | `msds:index_msds`<br>`msds:list_msds` |
| **Registrar una ficha** | Administrador de Laboratorio, Técnico de Laboratorio, SGA | `msds.add_msdsobject` | — | `msds:sds_create` |
| **Verificar la trazabilidad de las fichas extraídas** | SGA, Regente, Administrativo superior | `sga.view_sdstraceability` | — | `msds:verified_sds` |

### `DERB-01` — Construir un formulario dinámico

*derb · ui · prioridad P3 · cobertura por ruta: parcial · Selenium: sí*

El constructor de formularios sobre Formio.js: se arrastran campos, se agrupan en secciones y se previsualiza el resultado. Todo el valor está en el arrastrar y soltar del navegador, así que es de los pocos sitios donde una prueba Selenium es la única que puede decir algo.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Listar los formularios de la organización** | Administrador de Laboratorio, Administrativo superior, Profesor | `derb.view_customform` | — | `derb:form_list` |
| **Crear un formulario** | Administrador de Laboratorio, Administrativo superior | `derb.add_customform` | — | `derb:create_form` |
| **Editar el formulario en el constructor** | Administrador de Laboratorio, Administrativo superior | `derb.change_customform` | — | `derb:edit_view`<br>`derb:update_form` |
| **Previsualizar el formulario tal como lo verá quien lo rellene** | Administrador de Laboratorio, Administrativo superior, Profesor | `derb.view_customform` | — | `derb:preview_form` |
| **Borrar un formulario** | Administrador de Laboratorio, Administrativo superior | `derb.delete_customform` | — | `derb:delete_form` |

### `GEN-01` — Entrar al sistema y orientarse

*presentation · ui · prioridad P4 · cobertura por ruta: parcial · Selenium: sí*

La portada, la información general, los documentos de regulación y la pantalla de acceso denegado. Es lo que ve alguien que todavía no ha elegido organización.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Abrir la portada y la información general** | Anónimo, Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — | — | `index`<br>`general_info`<br>`home` |
| **Consultar y descargar los documentos de regulación** | Anónimo, Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — | — | `regulation_docs`<br>`download_all_regulations` |
| **Ver la pantalla de acceso denegado** | Anónimo, Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — | — | `permission_denied`<br>`error_view` |

Hallazgos:

- `HandleErrorMiddleware` convierte los 403 y 404 de peticiones HTML en un 302 hacia `error_view`. Es la razón por la que el smoke imprime el `Location` de cada redirección: sin verlo no se distingue «la página no existe» de «no tenés permiso».

### `GEN-02` — Seguir los tutoriales guiados y dar retroalimentación

*presentation · ui · prioridad P4 · cobertura por ruta: parcial · Selenium: sí*

El sistema de tutoriales contextuales: se listan, se marca el progreso, se apagan si molestan y se pueden reactivar. Más el formulario de retroalimentación del producto.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Ver los tutoriales disponibles** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | `auth_and_perms.institution_can_access` | — | `tutorials` |
| **Marcar progreso, apagar y reactivar un tutorial** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — | — | `tutorial_progress_api`<br>`tutorial_toggle_api`<br>`tutorial_reactivate_api` |
| **Enviar retroalimentación sobre el producto** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | `auth_and_perms.institution_can_access` | — | `feedback` |

### `REP-01` — Pedir un reporte, esperar a que se genere y descargarlo

*report · ui · prioridad P1 · cobertura por ruta: parcial · Selenium: —*

El ciclo asíncrono común a los dieciséis tipos de reporte: se elige el laboratorio y el formato, se encola la tarea, el panel consulta el estado hasta que termina y entonces se abre la tabla o se baja el fichero. Lo que justifica una prueba de navegador aquí es justamente ese ciclo: no se puede comprobar con un `client.get()`.

Estados que atraviesa:

- `TaskReport / DocumentReportStatus: "On hold" → "Generated" → "Delivered" (`report/models.py:10-18`)`

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Elegir el reporte y sus parámetros** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | `laboratory.do_report` | — | `report:reports_objects_list`<br>`report:reports_limited_shelf_objects_list`<br>`report:reactive_precursor_object_list`<br>`report:object_change_logs`<br>`report:waste_report`<br>`report:reactive_report`<br>`report:risk_zone_report`<br>`report:reactive_stock_report`<br>`report:reports_furniture_detail`<br>`report:compatibility_report`<br>`report:hazard_map_report`<br>`report:donations_report` |
| **Encolar la generación del reporte** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | `laboratory.do_report` | crea TaskReport en "On hold" | `report:create_report_request`<br>`report:create_organization_report_request` |
| **Consultar el estado hasta que la tarea termina** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | `laboratory.do_report` | — | `report:report_status`<br>`report:report_organization_status` |
| **Abrir el resultado en pantalla** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | `laboratory.do_report` | — | `report:report_table`<br>`report:report_organization_table` |
| **Descargar el fichero generado** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | `laboratory.do_report` | "Generated" → "Delivered" | `report:generate_report`<br>`report:generate_organization_report` |

Hallazgos:

- Dieciséis tipos de reporte por cinco formatos (`html`, `pdf`, `xls`, `xlsx`, `ods`) declarados en `report/register.py` `REPORT_FORMS`: **80 combinaciones** que se cubren recorriendo el registro con `subTest`, no con ochenta escenarios de navegador.
- HALLAZGO-REP-1: `TaskReport.STATUS_TEMPLATE` (`report/models.py:10-18`) usa **cadenas traducidas como claves** de choice: el valor que se persiste depende del idioma activo de quien genera el reporte.
- `report_status` y `report_organization_status` son dos nombres para la misma URL (`urls.py:21,39`). Es deliberado y benigno: ambos resuelven.

### `REP-02` — Llevar el control de precursores y presentar su reporte mensual

*report · ui · prioridad P1 · cobertura por ruta: parcial · Selenium: sí*

Los precursores tienen su propia pantalla y su propio ciclo, con valores que se registran por periodo. Es obligación regulatoria, no un reporte más: por eso tiene plantilla propia y una tarea mensual que lo prepara.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Consultar el reporte de precursores y sus valores** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | `laboratory.do_report` | — | `report:precursor_report`<br>`report:precursor_report_values_view` |

### `REP-03` — Presentar el reporte de regencia

*report · ui · prioridad P2 · cobertura por ruta: **sin prueba** · Selenium: —*

El informe propio del Regente Químico, con formulario y plantilla distintos del resto.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Generar el reporte de regencia** | Regente, Administrativo superior | `laboratory.do_report` | — | `report:regency_report` |

### `REP-04` — Ver el mapa de peligros sobre el plano

*report · ui · prioridad P2 · cobertura por ruta: **sin prueba** · Selenium: —*

La representación visual del riesgo por zona: un plano con la capa de peligros encima. Es estado en el cliente, y lo único del módulo que se consulta con `view_report` en vez de `do_report`.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Abrir el mapa de peligros** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | `laboratory.view_report` | — | `report:hazard_map_visual` |

### `RES-01` — Reservar material y llevar la reserva hasta su devolución

*reservations_management · ui · prioridad P1 · cobertura por ruta: parcial · Selenium: sí*

Un usuario del laboratorio pide una cantidad de un `ShelfObject` para un rango de fechas. Un gestor acepta o rechaza la reserva completa, o producto por producto. Al aceptar se descuenta el stock. Al terminar, alguien registra la devolución y el stock vuelve. La reserva se cierra cuando ya no queda nada vivo en ella.

Estados que atraviesa:

- `Reservations.status: REQUESTED(0) → ACCEPTED(1) | DENIED(2) → CLOSED(3)`
- `ReservedProducts.status: SELECTED(3) → REQUESTED(0) → BORROWED(1) | DENIED(2) → RETURNED(4)`

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Reservar desde el estante (reserva directa)** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | `laboratory.add_shelfobject` | → ReservedProducts.status=REQUESTED(0) | `laboratory:object_reservation` |
| **Solicitar la reserva desde un procedimiento** | Profesor, Estudiante | `reservations_management.add_reservedproducts` | → Reservations(is_massive=True) con sus ReservedProducts | `academic:generate_reservation` |
| **Consultar mis reservas** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | `reservations_management.view_reservedproducts` | — | `laboratory:my_reservations` |
| **Ver la cola de reservas por estado** | Administrador de Laboratorio, Administrativo de centro de trabajo, Asistente de laboratorio, Regente, Solo Lectura | `reservations_management.view_reservations` | — | `reservations_management:reservations_list` |
| **Aceptar o rechazar la reserva completa** | Administrador de Laboratorio, Administrativo de centro de trabajo, Asistente de laboratorio | `reservations_management.change_reservations` | REQUESTED → ACCEPTED | DENIED; productos → BORROWED | DENIED | `reservations_management:manage_reservation` |
| **Aceptar o rechazar un producto suelto de la reserva** | Administrador de Laboratorio, Administrativo de centro de trabajo, Asistente de laboratorio | `reservations_management.change_reservedproducts` | ReservedProducts.status → BORROWED | DENIED | `reservations_management:product_action` |
| **Registrar la devolución y reponer el stock** | Administrador de Laboratorio, Técnico de Laboratorio | `reservations_management.change_reservedproducts` | BORROWED → RETURNED(4), stock devuelto al ShelfObject | `reservations_management:return_product`<br>`reservations_management:increase_stock` |
| **Cerrar la reserva** | Administrador de Laboratorio | `reservations_management.change_reservations` | → CLOSED(3) | `reservations_management:close_reservation` |
| **Comprobar cantidad y disponibilidad antes de confirmar** | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo de centro de trabajo | — | — | `reservations_management:validate_reservation`<br>`reservations_management:get_product_name_and_quantity` |

Hallazgos:

- HALLAZGO-RES-1: `ManageReservationView` (views.py:60) no revalida el laboratorio. El filtro `get_lab_ids` solo existe en el listado (views.py:44), así que un gestor puede aprobar una reserva de un laboratorio sobre el que no tiene alcance.
- HALLAZGO-RES-2: quien entrega y quien recibe la devolución comparten `change_reservedproducts`; quien aprueba y quien cierra comparten `change_reservations`. Los cuatro actores del negocio son dos permisos.
- HALLAZGO-RES-3: `ACCEPTED == BORROWED == 1` y `CLOSED == SELECTED == 3` (models.py:9-14): comparar `status` sin saber de qué modelo es acierta por accidente.
- HALLAZGO-RES-4: **la misma acción entra por dos permisos que no tienen nada que ver.** Reservar desde el estante exige `laboratory.add_shelfobject` (`reservation.py:23`) —un permiso de inventario: quien puede reservar es, por construcción, quien puede meter cosas en un estante—, mientras que reservar desde un procedimiento exige `reservations_management.add_reservedproducts` (`academic/views.py:606-609`). Un rol al que se le dé el permiso de reservas seguirá sin poder reservar desde el estante, y uno que solo gestione inventario podrá reservar sin tener ningún permiso de reservaciones.
- Ver «mis reservas» exige `view_reservedproducts` mientras que ver la cola exige `view_reservations`: son dos permisos distintos para dos vistas del mismo dato, lo que sí separa correctamente al solicitante del gestor.

### `RES-02` — Iniciar y expirar reservas automáticamente

*reservations_management · celery · prioridad P2 · cobertura por ruta: **sin prueba** · Selenium: —*

El planificador marca como prestados los productos cuya reserva empieza y deniega los que expiran sin stock disponible. Es el único actor del flujo que no es una persona, y no lo cubre ninguna prueba de navegador.

Estados que atraviesa:

- `Reservations.status: REQUESTED(0) → ACCEPTED(1) | DENIED(2) → CLOSED(3)`
- `ReservedProducts.status: SELECTED(3) → REQUESTED(0) → BORROWED(1) | DENIED(2) → RETURNED(4)`

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Marcar como prestado al llegar la fecha de inicio** | Sistema | — | → BORROWED(1) | — |
| **Denegar la reserva que expira sin stock** | Sistema | — | → DENIED(2) | — |

### `RISK-01` — Definir las zonas de riesgo de la organización

*risk_management · ui · prioridad P2 · cobertura por ruta: parcial · Selenium: sí*

El mapa de dónde está el peligro: se dan de alta las zonas, su tipo y sus restricciones de prioridad, se asocian a laboratorios y se consultan en un panel con su reporte.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Listar y abrir el detalle de una zona de riesgo** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio | `risk_management.view_riskzone` | — | `riskmanagement:riskzone_list`<br>`riskmanagement:riskzone_detail` |
| **Crear una zona de riesgo y su tipo** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio | `risk_management.add_riskzone`<br>`risk_management.add_zonetype` | — | `riskmanagement:riskzone_create`<br>`riskmanagement:zone_type_add` |
| **Editar o borrar una zona** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio | `risk_management.change_riskzone`<br>`risk_management.delete_riskzone` | — | `riskmanagement:riskzone_update`<br>`riskmanagement:riskzone_delete` |
| **Ver el panel de zonas y su reporte** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio | `laboratory.view_report` | — | `riskmanagement:zone_dashboard`<br>`riskmanagement:risk_report` |
| **Consultar las jornadas de trabajo de la zona** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio | `risk_management.view_workday` | — | `riskmanagement:workday_list` |

Hallazgos:

- `zone_dashboard` no declara ningún permiso inspeccionable, a diferencia del resto del módulo.

### `RISK-02` — Reportar y dar seguimiento a un incidente

*risk_management · ui · prioridad P2 · cobertura por ruta: parcial · Selenium: sí*

Alguien registra lo que pasó en un laboratorio, se consulta el histórico y se descarga el reporte. **No hay flujo de aprobación**: el incidente no tiene estado ni quien lo valide, solo el CRUD y sus permisos.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Registrar un incidente** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio, Estudiante, Profesor | `risk_management.add_incidentreport` | — | `riskmanagement:incident_create` |
| **Listar incidentes y abrir su detalle** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio | `risk_management.view_incidentreport` | — | `riskmanagement:incident_list`<br>`riskmanagement:incident_detail` |
| **Corregir o eliminar un incidente** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio | `risk_management.change_incidentreport`<br>`risk_management.delete_incidentreport` | — | `riskmanagement:incident_update`<br>`riskmanagement:incident_delete` |
| **Descargar el reporte de incidentes** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio | `laboratory.do_report` | — | `riskmanagement:incident_report` |

Hallazgos:

- HALLAZGO-RISK-1: el incidente no tiene estado ni aprobador (`models.py:120`). Quien lo reporta y quien lo corrige se distinguen solo por `add` frente a `change`; nadie lo cierra ni lo valida.

### `RISK-03` — Mantener edificios, estructuras y regentes

*risk_management · ui · prioridad P3 · cobertura por ruta: **sin prueba** · Selenium: sí*

Los datos maestros del módulo: los edificios y sus estructuras físicas, y el registro de regentes con su tipo profesional. El regente importa más allá de este módulo: es destinatario implícito de tareas pendientes.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Listar, crear y editar edificios** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio | `risk_management.view_buildings`<br>`risk_management.add_buildings` | — | `riskmanagement:buildings_list`<br>`riskmanagement:buildings_create`<br>`riskmanagement:buildings_update` |
| **Listar, crear y editar estructuras** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio | `risk_management.view_structure`<br>`risk_management.add_structure` | — | `riskmanagement:structures_list`<br>`riskmanagement:structures_create`<br>`riskmanagement:structures_update` |
| **Consultar los regentes del laboratorio** | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio | `risk_management.view_regent` | — | `riskmanagement:regents` |

Hallazgos:

- Editar un edificio o una estructura exige `add_*`, no `change_*` (`buildings_actions`, `structure_actions`): la vista de alta y la de edición son la misma y comparten el permiso de alta. Un rol al que se le quiera dar solo edición no se puede configurar.

### `IPER-01` — Solicitar, llenar y auditar una evaluación IPER

*risk_management · ui · prioridad P1 · cobertura por ruta: parcial · Selenium: —*

El flujo de la norma INTE T55, y el que mejor separa actores de todo Organilab: alguien de la organización **solicita** a los laboratorios de una zona que llenen su IPER —lo que genera una tarea pendiente para cada responsable—, el laboratorio la **llena** identificando peligros y valorando el riesgo, la marca como completada, y un auditor externo la **observa** sin poder modificarla. Al revisarla se clona la versión anterior, que queda obsoleta.

Estados que atraviesa:

- `IPERAssessment.status: "draft" → "completed" → "obsolete" (`risk_management/models.py:470-476`)`

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Solicitar a los laboratorios de una zona que llenen su IPER** | Administrador IPER, Administrativo superior | `risk_management.request_iper` | crea una PendingTask por laboratorio, dirigida al responsable de cada uno | `riskmanagement:iper_request_zone` |
| **Crear la evaluación del laboratorio** | Administrador de Laboratorio, Regente asignado al laboratorio, Administrador IPER | `risk_management.add_iperassessment` | → status="draft" | `riskmanagement:iper_create` |
| **Identificar peligros y valorar el riesgo** | Administrador de Laboratorio, Regente asignado al laboratorio, Administrador IPER | `risk_management.change_iperassessment` | — | `riskmanagement:iper_hazard_create`<br>`riskmanagement:iper_hazard_update`<br>`riskmanagement:iper_hazard_delete`<br>`riskmanagement:iper_update` |
| **Marcar la evaluación como completada (o devolverla a borrador)** | Administrador de Laboratorio, Regente asignado al laboratorio, Administrador IPER | `risk_management.change_iperassessment` | "draft" ⇄ "completed"; una obsoleta ya no puede cambiar (`iper_views.py:350-360`) | `riskmanagement:iper_toggle_status` |
| **Clonar la evaluación para actualizarla** | Administrador de Laboratorio, Regente asignado al laboratorio, Administrador IPER | `risk_management.add_iperassessment` | la versión anterior pasa a "obsolete" | `riskmanagement:iper_clone` |
| **Observar la evaluación sin poder modificarla** | Auditor IPER | `risk_management.add_iperobservation` | — | `riskmanagement:iper_observation_add` |
| **Listar evaluaciones, ver el detalle y su histórico** | Auditor IPER, Administrador IPER, Administrador de Laboratorio, Regente, Solo Lectura | `risk_management.view_iperassessment` | — | `riskmanagement:iper_list`<br>`riskmanagement:iper_detail`<br>`riskmanagement:iper_history`<br>`riskmanagement:iper_lab_help` |
| **Ver el panel consolidado de IPER** | Administrador IPER, Administrativo superior, Auditor IPER | `risk_management.view_iper_dashboard` | — | `riskmanagement:iper_dashboard` |
| **Alternar el anonimato de la evaluación** | Administrador de Laboratorio, Administrador IPER | `risk_management.change_iperassessment` | — | `riskmanagement:iper_toggle_anonymous` |
| **Mantener el catálogo IPER de la organización raíz** | Administrador IPER | `risk_management.manage_iper_catalog` | — | `riskmanagement:iper_catalog_add` |
| **Eliminar una evaluación** | Administrador IPER, Administrativo superior | `risk_management.delete_iperassessment` | — | `riskmanagement:iper_delete` |

Hallazgos:

- Es el flujo con la separación de actores mejor implementada del sistema: cuatro permisos propios (`view_all_iper`, `request_iper`, `view_iper_dashboard`, `manage_iper_catalog`, `models.py:531-539`) y dos roles dedicados que además **se autocrean** si no existen (`update_roles.py:1231,1254`), a diferencia del resto del catálogo de roles. Al `Auditor IPER` se le retira `view_riskzone` a propósito (`:1243`): puede auditar la evaluación sin ver el mapa de zonas.
- Contraste con RES-01: aquí solicitar, llenar y auditar son tres permisos distintos; en reservaciones, cuatro actores del negocio son dos permisos.

### `IPER-02` — Recordar por correo las evaluaciones IPER que toca actualizar

*risk_management · celery · prioridad P3 · cobertura por ruta: **sin prueba** · Selenium: —*

Cada mañana el planificador busca las evaluaciones periódicas cuyo plazo vence y avisa a quien tiene que actualizarlas.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Enviar los recordatorios de actualización** | Sistema | — | crea PendingTask y envía correo a los responsables | — |

### `RISK-04` — Generar la bitácora diaria de establecimientos

*risk_management · celery · prioridad P3 · cobertura por ruta: **sin prueba** · Selenium: —*

Tarea programada que consolida los registros de establecimiento del día. No tiene pantalla: solo se observa por sus efectos.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Crear los reportes de establecimiento** | Sistema | — | — | — |

### `SGA-01` — Registrar una sustancia y llevarla hasta su aprobación

*sga · ui · prioridad P1 · cobertura por ruta: completa · Selenium: sí*

Un redactor abre el asistente, describe la sustancia y sus características, completa la ficha de seguridad y la manda a revisión. Un revisor la mira en la bandeja, deja observaciones si hace falta, y la aprueba: al aprobarla se emiten los códigos de sustancia-laboratorio y se crea el objeto de inventario correspondiente.

Estados que atraviesa:

- `Substance.status: DRAFT(0) → UNDER_REVIEW(1) → APPROVED(2) (`sga/models.py:129-136`)`
- `ReviewSubstance.is_approved: False → True (`sga/models.py:900`)`

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Abrir el asistente y describir la sustancia (paso 1)** | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Lectura y agregado de sustancias, Manejo de sustancias del laboratorio | `laboratory.change_object`<br>`auth_and_perms.institution_can_access` | crea Substance en DRAFT(0) en el primer POST válido | `sga:create_sustance`<br>`sga:step_one`<br>`sga:update_substance` |
| **Completar la hoja de seguridad (paso 4)** | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Lectura y agregado de sustancias, Manejo de sustancias del laboratorio | `sga.change_securityleaf`<br>`auth_and_perms.institution_can_access` | — | `sga:step_four` |
| **Subir la ficha de datos de seguridad y seguir la extracción** | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Lectura y agregado de sustancias, Manejo de sustancias del laboratorio | `sga.change_substancecharacteristics`<br>`auth_and_perms.institution_can_access` | dispara la tarea de extracción; el estado se consulta por polling | `sga:upload_sds`<br>`sga:upload_sds_pk`<br>`sga:sds_task_status` |
| **Añadir el proveedor de la sustancia** | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Lectura y agregado de sustancias, Manejo de sustancias del laboratorio | `sga.add_provider` | — | `sga:add_sga_provider` |
| **Enviar la sustancia a revisión** | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Lectura y agregado de sustancias, Manejo de sustancias del laboratorio | `sga.change_substance`<br>`auth_and_perms.institution_can_access` | DRAFT(0) → UNDER_REVIEW(1); notifica a los revisores | `sga:send_to_review` |
| **Ver la bandeja de sustancias por aprobar** | Administrativo superior, SGA, Organization Management | `sga.view_substance`<br>`auth_and_perms.institution_can_access` | — | `sga:approved_substance`<br>`sga:get_substance` |
| **Dejar, editar o borrar observaciones sobre la sustancia** | Administrativo superior, SGA, Organization Management, Administrador de Laboratorio | `sga.view_substanceobservation`<br>`sga.change_substanceobservation`<br>`sga.delete_substanceobservation` | — | `sga:add_observation`<br>`sga:update_observation`<br>`sga:delete_observation` |
| **Abrir el detalle de la sustancia en revisión** | Administrativo superior, SGA, Organization Management | `sga.change_substance`<br>`auth_and_perms.institution_can_access` | — | `sga:detail_substance` |
| **Aprobar la sustancia** | Administrativo superior, SGA, Organization Management | `sga.change_substance`<br>`auth_and_perms.institution_can_access` | ReviewSubstance.is_approved=True y Substance.status=APPROVED(2); emite códigos y crea el objeto de inventario | `sga:accept_substance` |
| **Eliminar la sustancia** | Administrativo superior, SGA, Organization Management, Administrador de Laboratorio | `sga.delete_substance`<br>`auth_and_perms.institution_can_access` | — | `sga:delete_substance` |

Hallazgos:

- HALLAZGO-SGA-1: **el revisor no es un rol.** `notify_request_created` (`sga/utils.py:52-57`) busca a quién avisar en el grupo de Django `RegisterOrganization`, no en un `Rol` ni en un `ProfilePermission`. El actor que aprueba sustancias vive en la capa 4 del modelo de autorización, fuera del eje de roles, y por eso ninguna prueba de permisos por `Rol` puede cubrirlo.
- HALLAZGO-SGA-2: `approve_substances` es alcanzable por GET y la idempotencia depende de una guardia escrita a mano (`views.py:215-221`). Sin esa guardia, recargar la página volvería a emitir códigos. Merece su propia aserción.
- HALLAZGO-SGA-3: crear una sustancia exige `laboratory.change_object`, no `sga.add_substance` (`views.py:58`). El permiso que el nombre haría esperar no interviene, así que un rol con todo SGA pero sin permisos de laboratorio no puede registrar una sustancia.

### `SGA-02` — Obtener la etiqueta GHS y la ficha de seguridad de una sustancia

*sga · ui · prioridad P1 · cobertura por ruta: **sin prueba** · Selenium: sí*

Desde el detalle de la sustancia se genera la etiqueta con sus pictogramas y frases H/P, y se descarga la hoja de seguridad en PDF. Es el producto final del módulo: lo que acaba pegado en el envase.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Generar la etiqueta de la sustancia** | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Regente, Solo Lectura, Estudiante | `sga.view_substance`<br>`auth_and_perms.institution_can_access` | — | `sga:generate_label` |
| **Descargar la hoja de seguridad en PDF** | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Regente, Solo Lectura, Estudiante | `auth_and_perms.institution_can_access` | — | `sga:security_leaf_pdf` |
| **Consultar los complementos SGA de una sustancia** | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Regente, Solo Lectura, Estudiante | — | — | `sga:get_sgacomplement_by_substance` |

### `SGA-03` — Mantener el catálogo de clasificación GHS

*sga · ui · prioridad P2 · cobertura por ruta: parcial · Selenium: —*

Alta y edición de las indicaciones de peligro (frases H), los consejos de prudencia (frases P), las palabras de advertencia y las categorías de sustancia peligrosa. Es el catálogo del que bebe toda la clasificación: sin él, ninguna etiqueta dice nada.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Consultar frases H, frases P y palabras de advertencia** | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Regente, Solo Lectura, Estudiante | `sga.view_dangerindication`<br>`sga.view_prudenceadvice`<br>`sga.view_warningword` | — | `sga:danger_indications`<br>`sga:prudence_advices`<br>`sga:warning_words` |
| **Dar de alta una frase o palabra de advertencia** | SGA, Administrativo superior | — | — | `sga:add_danger_indication`<br>`sga:add_prudence_advice`<br>`sga:add_warning_word` |
| **Editar una frase o palabra de advertencia** | SGA, Administrativo superior | `sga.change_dangerindication`<br>`sga.change_prudenceadvice`<br>`sga.change_warningword` | — | `sga:update_danger_indication`<br>`sga:update_prudence_advice`<br>`sga:update_warning_word` |
| **Consultar sustancias peligrosas y sus categorías** | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Regente, Solo Lectura, Estudiante | `sga.view_dangersubstance`<br>`sga.view_dangersubstancecategory` | — | `sga:danger_substance`<br>`sga:danger_substance_category` |

Hallazgos:

- El alta de complementos (`add_sga_complements`) no declara permiso inspeccionable, mientras que la edición sí. Crear una frase H es más fácil que corregirla.

### `SGA-04` — Diseñar plantillas de etiqueta en el editor SGA

*sga · ui · prioridad P2 · cobertura por ruta: **sin prueba** · Selenium: sí*

El editor visual con el que se compone una plantilla de etiqueta: se eligen los bloques, se previsualiza, se ajusta el tamaño del recipiente y se guarda como plantilla personal o de la organización. Es todo estado en el cliente, así que es de los pocos sitios donde Selenium se gana el sueldo.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Abrir el editor de plantillas** | SGA, Administrativo superior, Administrador de Laboratorio | `auth_and_perms.institution_can_access` | — | `sga:editor`<br>`sga:index_editor` |
| **Crear una plantilla personal** | SGA, Administrativo superior, Administrador de Laboratorio | `sga.add_displaylabel`<br>`auth_and_perms.institution_can_access` | — | `sga:add_personal`<br>`sga:sgalabel_create` |
| **Editar la plantilla paso a paso** | SGA, Administrativo superior, Administrador de Laboratorio | `sga.change_displaylabel`<br>`auth_and_perms.institution_can_access` | — | `sga:edit_personal`<br>`sga:sgalabel_step_one`<br>`sga:sgalabel_step_two` |
| **Previsualizar la etiqueta y su código de barras** | SGA, Administrativo superior, Administrador de Laboratorio | — | — | `sga:get_preview`<br>`sga:engine_label_preview`<br>`sga:barcode_from_number` |
| **Borrar una plantilla** | SGA, Administrativo superior | `sga.delete_displaylabel`<br>`auth_and_perms.institution_can_access` | — | `sga:delete_sgalabel` |

### `SGA-05` — Gestionar empresas y tamaños de recipiente del etiquetado

*sga · ui · prioridad P3 · cobertura por ruta: **sin prueba** · Selenium: —*

Los datos maestros que la etiqueta imprime: la empresa que figura como responsable y los tamaños de recipiente que determinan la escala de la etiqueta.

| Paso | Actores | Permiso | Transición | Rutas |
|---|---|---|---|---|
| **Listar y consultar empresas** | SGA, Administrativo superior, Administrador de Laboratorio | `sga.view_builderinformation`<br>`auth_and_perms.institution_can_access` | — | `sga:get_companies`<br>`sga:get_company` |
| **Crear o editar una empresa** | SGA, Administrativo superior | `sga.add_builderinformation`<br>`sga.change_builderinformation`<br>`auth_and_perms.institution_can_access` | — | `sga:add_company`<br>`sga:edit_company` |
| **Quitar una empresa** | SGA, Administrativo superior | `sga.delete_builderinformation`<br>`auth_and_perms.institution_can_access` | — | `sga:remove_company` |
| **Consultar y dar de alta tamaños de recipiente** | SGA, Administrativo superior, Administrador de Laboratorio, Depositante de residuos | `sga.view_recipientsize`<br>`sga.view_builderinformation`<br>`auth_and_perms.institution_can_access` | — | `sga:recipient_size`<br>`sga:add_recipient_size`<br>`sga:get_recipient_size` |

## Roles y quién los ejercita

| Rol | En el catálogo | Definido en |
|---|:-:|---|
| Estudiante | sí | `auth_and_perms/management/commands/update_roles.py:30` |
| Depositante de residuos | sí | `auth_and_perms/management/commands/update_roles.py:47` |
| Creador de laboratorio | sí | `auth_and_perms/management/commands/update_roles.py:163` |
| Administrador de Laboratorio | sí | `auth_and_perms/management/commands/update_roles.py:212` |
| Lectura y agregado de sustancias | sí | `auth_and_perms/management/commands/update_roles.py:265` |
| Asistente de laboratorio | sí | `auth_and_perms/management/commands/update_roles.py:450` |
| Profesor | sí | `auth_and_perms/management/commands/update_roles.py:531` |
| Tesista modulo desechos | sí | `auth_and_perms/management/commands/update_roles.py:581` |
| Solo Lectura | sí | `auth_and_perms/management/commands/update_roles.py:756` |
| Técnico de Laboratorio | sí | `auth_and_perms/management/commands/update_roles.py:828` |
| SGA | sí | `auth_and_perms/management/commands/update_roles.py:948` |
| Regente | sí | `auth_and_perms/management/commands/update_roles.py:979` |
| Administrativo superior | sí | `auth_and_perms/management/commands/update_roles.py:1005` |
| Administrativo de centro de trabajo | sí | `auth_and_perms/management/commands/update_roles.py:1030` |
| Auditor IPER | sí | `auth_and_perms/management/commands/update_roles.py:1231` |
| Administrador IPER | sí | `auth_and_perms/management/commands/update_roles.py:1254` |
| Manejo de sustancias del laboratorio | sí | `auth_and_perms/management/commands/add_static_rol.py:17` |
| Organization Management | sí | `auth_and_perms/views/user_org_creation.py:95` |

Los pseudo-roles no conceden permisos y se listan aparte:

| Actor | Capa | Cuenta como cobertura |
|---|---|:-:|
| Superusuario | `superusuario` | **no** |
| Administrador de la organización | `tipo_en_organizacion` | **no** |
| Gestor de laboratorio | `tipo_en_organizacion` | **no** |
| Usuario de laboratorio | `tipo_en_organizacion` | **no** |
| Responsable del laboratorio | `campo` | **no** |
| Regente asignado al laboratorio | `campo` | **no** |
| Sistema | `sistema` | **no** |
| Anónimo | `sistema` | **no** |

## Apps pendientes de catalogar

| App | Motivo |
|---|---|
| `djgentelella` | biblioteca de terceros: sus rutas no son funcionalidades de Organilab |
| `rest_framework` | biblioteca de terceros |

## Excepciones

Rutas navegables que a propósito no pertenecen a ninguna funcionalidad.

| Ruta | Motivo |
|---|---|

