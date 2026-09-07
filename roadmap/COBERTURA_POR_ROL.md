# Cobertura por rol

Generado por `make feature-coverage`. No editar a mano: se regenera.

Esto **no** sale de leer las pruebas, sale de observarlas: la sonda de
`presentation/probe.py` anota cada petición HTTP de la suite con los `Rol`
que el usuario tenía en el ámbito de esa URL, resueltos con el mismo `Q` que
usa `ProfileMiddleware` para autorizar.

> **Una petición ejecutada por un superusuario no cuenta como cobertura de
> ningún rol.** El middleware se salta a los superusuarios
> (`authentication/middleware.py:49-50`), así que esa prueba ejercita la
> interacción, no el permiso.

Los `Rol` que solo existen en las fixtures —los «Gestión de X» de
`base_selenium.json`— tampoco cuentan: no existen en producción.

## Resumen

| Estado del paso | Pasos |
|---|---:|
| ejercitado | 8 |
| fuera del alcance de la sonda | 9 |
| nunca ejercitado | 21 |
| solo superusuario | 131 |
| **peticiones observadas** | **4905** |

## Roles canónicos

| Rol | Pasos ejercitados |
|---|---:|
| Estudiante | 1 |
| Depositante de residuos | 0 |
| Creador de laboratorio | 0 |
| Administrador de Laboratorio | 6 |
| Lectura y agregado de sustancias | 0 |
| Asistente de laboratorio | 0 |
| Profesor | 2 |
| Tesista modulo desechos | 0 |
| Solo Lectura | 0 |
| Técnico de Laboratorio | 0 |
| SGA | 0 |
| Regente | 0 |
| Administrativo superior | 0 |
| Administrativo de centro de trabajo | 0 |
| Auditor IPER | 0 |
| Administrador IPER | 0 |
| Manejo de sustancias del laboratorio | 0 |
| Organization Management | 0 |

**Sin ejercitar ni una vez:** Depositante de residuos, Creador de laboratorio, Lectura y agregado de sustancias, Asistente de laboratorio, Tesista modulo desechos, Solo Lectura, Técnico de Laboratorio, SGA, Regente, Administrativo superior, Administrativo de centro de trabajo, Auditor IPER, Administrador IPER, Manejo de sustancias del laboratorio, Organization Management.

## Pasos por funcionalidad

### `ACAD-01` — Diseñar una plantilla de procedimiento con sus pasos

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Crear la plantilla del procedimiento | solo superusuario | Profesor, Administrador de Laboratorio, Asistente de laboratorio | — |
| Listar y consultar plantillas | solo superusuario | Profesor, Administrador de Laboratorio, Asistente de laboratorio, Estudiante, Solo Lectura | — |
| Editar la plantilla | solo superusuario | Profesor, Administrador de Laboratorio, Asistente de laboratorio | — |
| Añadir pasos a la plantilla | solo superusuario | Profesor, Administrador de Laboratorio, Asistente de laboratorio | — |
| Editar un paso | solo superusuario | Profesor, Administrador de Laboratorio, Asistente de laboratorio | — |
| Borrar un paso o la plantilla completa | solo superusuario | Profesor, Administrador de Laboratorio, Asistente de laboratorio | — |

### `ACAD-02` — Ejecutar un procedimiento y reservar el material que necesita

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Crear mi procedimiento a partir de una plantilla | solo superusuario | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | — |
| Ver mis procedimientos | ejercitado | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | Profesor |
| Generar la reserva de todo el material del procedimiento | solo superusuario | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | — |
| Completar los pasos y cambiar el estado | solo superusuario | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | — |
| Quitar mi procedimiento | solo superusuario | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | — |

### `ORG-01` — Elegir organización y orientarse en el árbol

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Elegir la organización con la que se trabaja | solo superusuario | Estudiante, Profesor, Técnico de Laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — |
| Ver el mapa de laboratorios | solo superusuario | Administrador de Laboratorio, Administrativo superior, Regente | — |
| Listar organizaciones y sus laboratorios | solo superusuario | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | — |

### `ORG-02` — Administrar la organización: usuarios, roles y estructura

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Abrir el gestor de la organización | solo superusuario | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | — |
| Añadir usuarios a la organización | solo superusuario | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | — |
| Consultar, crear y editar los roles de la organización | solo superusuario | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | — |
| Quitar un rol de la organización | solo superusuario | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | — |
| Copiar el juego de roles a otra organización | solo superusuario | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | — |
| Habilitar organizaciones hijas y relacionar modelos | solo superusuario | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | — |
| Consultar quién administra la organización | nunca ejercitado | Administrativo superior, Organization Management, Administrador de Laboratorio, Administrativo de centro de trabajo | — |

### `ORG-03` — Entrar con firma digital o segundo factor

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Autenticarse con la firma digital del BCCR | nunca ejercitado | Anónimo | — |
| Obtener el QR del segundo factor | nunca ejercitado | Estudiante, Profesor, Administrador de Laboratorio | — |

### `ORG-04` — Suplantar a otro usuario para dar soporte

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Entrar como otro usuario | nunca ejercitado | Administrativo superior, Organization Management | — |
| Volver a la identidad propia | nunca ejercitado | Administrativo superior, Organization Management | — |

### `INV-01` — Mantener el catálogo de objetos: reactivos, materiales y equipos

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Listar sustancias, materiales y equipos | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — |
| Dar de alta un objeto en el catálogo | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | — |
| Editar o borrar un objeto del catálogo | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | — |
| Consultar los rasgos de los objetos | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — |
| Consultar los proveedores | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — |

### `INV-02` — Operar un objeto en el estante: crear, aumentar, disminuir, mover y desechar

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Ver los objetos de un estante | nunca ejercitado | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — |
| Colocar un objeto en el estante | nunca ejercitado | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Depositante de residuos | — |
| Abrir el detalle del objeto, con su QR | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — |
| Editar la cantidad, el límite y los datos del objeto | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante | — |
| Generar la etiqueta del objeto | nunca ejercitado | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — |
| Borrar o desechar el objeto | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Depositante de residuos, Tesista modulo desechos | — |
| Ver los reactivos del estante y su reorden | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | — |

### `INV-03` — Cargar inventario en masa desde un fichero

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Subir el fichero y previsualizar | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | — |
| Confirmar y crear los objetos en el estante | nunca ejercitado | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | — |

### `INV-04` — Vigilar existencias, vencimientos y límites

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Ver el panel de existencias de reactivos | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Regente | — |
| Silenciar los avisos de un objeto | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | — |

### `INV-05` — Vigilar el inventario automáticamente y avisar

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Avisar de los productos que llegaron a su límite | fuera del alcance de la sonda | Sistema | — |
| Registrar el stock máximo del día | fuera del alcance de la sonda | Sistema | — |
| Avisar por correo de los objetos por vencer | fuera del alcance de la sonda | Sistema | — |
| Preparar el reporte mensual de precursores | fuera del alcance de la sonda | Sistema | — |
| Limpiar las relaciones huérfanas organización-laboratorio | fuera del alcance de la sonda | Sistema | — |

### `INV-06` — Redactar y aprobar informes periódicos

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Programar el periodo de los informes | solo superusuario | Administrador de Laboratorio, Asistente de laboratorio | — |
| Crear el informe | solo superusuario | Administrador de Laboratorio, Asistente de laboratorio, Técnico de Laboratorio | — |
| Completar el informe y cambiar su estado | solo superusuario | Administrador de Laboratorio | — |
| Retirar un informe | solo superusuario | Administrador de Laboratorio | — |

### `INV-07` — Consultar los reportes de inventario del laboratorio

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Abrir el índice de reportes del laboratorio | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — |
| Consultar y descargar los reportes de códigos H | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — |
| Descargar el reporte de objetos en estantes | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — |
| Ver la cobertura de fichas de seguridad | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — |

### `INV-08` — Documentar protocolos del laboratorio

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Listar protocolos | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias, Estudiante, Profesor, Regente, Solo Lectura, Administrativo superior | — |
| Crear o editar un protocolo | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | — |
| Borrar un protocolo (va a la papelera) | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, Asistente de laboratorio, Lectura y agregado de sustancias | — |

### `LAB-01` — Crear y administrar una organización

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Crear la organización | solo superusuario | Administrativo superior, Organization Management | — |
| Editar la organización y sus acciones | solo superusuario | Administrativo superior, Organization Management | — |
| Borrar la organización | solo superusuario | Administrativo superior, Organization Management | — |

### `LAB-02` — Solicitar un laboratorio u organización y aprobarlo

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Pedir un laboratorio nuevo o una organización nueva | solo superusuario | Técnico de Laboratorio, Profesor, Asistente de laboratorio, Administrador de Laboratorio | — |
| Revisar la solicitud y aprobarla o rechazarla | solo superusuario | Administrativo superior | — |

### `LAB-03` — Crear un laboratorio y entrar a trabajar en él

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Crear el laboratorio | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — |
| Ver mis laboratorios y entrar en uno | ejercitado | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | Administrador de Laboratorio, Estudiante |
| Abrir la vista del laboratorio con su árbol de salas y estantes | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | — |
| Editar o borrar el laboratorio | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — |
| Consultar los procesos del laboratorio | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | — |

### `LAB-04` — Montar salas, muebles y estantes

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Listar, crear, editar y borrar salas | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — |
| Regenerar el QR de la sala | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — |
| Listar, crear, editar y borrar muebles | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — |
| Crear, editar y borrar estantes | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — |
| Ver los contenedores de un estante | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | — |
| Descargar el reporte de la sala | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | — |

### `LAB-05` — Mantener los catálogos del laboratorio

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Dar de alta una entrada de catálogo desde el formulario | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — |
| Consultar tipos de equipo y familias instrumentales | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | — |

### `LAB-06` — Dar de alta usuarios del laboratorio por código QR

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Generar y administrar los QR de registro | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — |
| Descargar el PDF con el QR | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — |
| Escanear el QR y quedar registrado en el laboratorio | nunca ejercitado | Estudiante, Profesor, Anónimo | — |
| Consultar quién entró por el QR | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — |
| Retirar un QR de registro | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio | — |

### `LAB-07` — Consultar la bitácora y recuperar lo borrado

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Consultar la bitácora de la organización | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Solo Lectura | — |
| Ver la papelera y recuperar un elemento | solo superusuario | Administrativo superior, Administrador de Laboratorio | — |

### `LAB-08` — Consultar y editar el perfil propio

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Ver y editar el perfil | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | — |
| Cambiar la contraseña | solo superusuario | Administrativo superior, Administrador de Laboratorio, Creador de laboratorio, Asistente de laboratorio, Técnico de Laboratorio, Estudiante, Profesor, Regente, Solo Lectura | — |

### `TASK-01` — Recibir y atender una tarea pendiente

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Ver mis tareas pendientes | solo superusuario | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — |

### `MSDS-01` — Consultar y verificar las fichas de seguridad del laboratorio

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Consultar el árbol de fichas | solo superusuario | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — |
| Registrar una ficha | solo superusuario | Administrador de Laboratorio, Técnico de Laboratorio, SGA | — |
| Verificar la trazabilidad de las fichas extraídas | solo superusuario | SGA, Regente, Administrativo superior | — |

### `DERB-01` — Construir un formulario dinámico

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Listar los formularios de la organización | solo superusuario | Administrador de Laboratorio, Administrativo superior, Profesor | — |
| Crear un formulario | solo superusuario | Administrador de Laboratorio, Administrativo superior | — |
| Editar el formulario en el constructor | solo superusuario | Administrador de Laboratorio, Administrativo superior | — |
| Previsualizar el formulario tal como lo verá quien lo rellene | solo superusuario | Administrador de Laboratorio, Administrativo superior, Profesor | — |
| Borrar un formulario | solo superusuario | Administrador de Laboratorio, Administrativo superior | — |

### `GEN-01` — Entrar al sistema y orientarse

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Abrir la portada y la información general | solo superusuario | Anónimo, Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — |
| Consultar y descargar los documentos de regulación | solo superusuario | Anónimo, Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — |
| Ver la pantalla de acceso denegado | solo superusuario | Anónimo, Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — |

### `GEN-02` — Seguir los tutoriales guiados y dar retroalimentación

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Ver los tutoriales disponibles | solo superusuario | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — |
| Marcar progreso, apagar y reactivar un tutorial | solo superusuario | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — |
| Enviar retroalimentación sobre el producto | solo superusuario | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo superior, Regente, Solo Lectura | — |

### `REP-01` — Pedir un reporte, esperar a que se genere y descargarlo

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Elegir el reporte y sus parámetros | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | — |
| Encolar la generación del reporte | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | — |
| Consultar el estado hasta que la tarea termina | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | — |
| Abrir el resultado en pantalla | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | — |
| Descargar el fichero generado | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | — |

### `REP-02` — Llevar el control de precursores y presentar su reporte mensual

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Consultar el reporte de precursores y sus valores | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | — |

### `REP-03` — Presentar el reporte de regencia

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Generar el reporte de regencia | solo superusuario | Regente, Administrativo superior | — |

### `REP-04` — Ver el mapa de peligros sobre el plano

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Abrir el mapa de peligros | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Administrativo de centro de trabajo | — |

### `RES-01` — Reservar material y llevar la reserva hasta su devolución

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Reservar desde el estante (reserva directa) | nunca ejercitado | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | — |
| Solicitar la reserva desde un procedimiento | solo superusuario | Profesor, Estudiante | — |
| Consultar mis reservas | ejercitado | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio | Profesor |
| Ver la cola de reservas por estado | ejercitado | Administrador de Laboratorio, Administrativo de centro de trabajo, Asistente de laboratorio, Regente, Solo Lectura | Administrador de Laboratorio |
| Aceptar o rechazar la reserva completa | ejercitado | Administrador de Laboratorio, Administrativo de centro de trabajo, Asistente de laboratorio | Administrador de Laboratorio |
| Aceptar o rechazar un producto suelto de la reserva | nunca ejercitado | Administrador de Laboratorio, Administrativo de centro de trabajo, Asistente de laboratorio | — |
| Registrar la devolución y reponer el stock | ejercitado | Administrador de Laboratorio, Técnico de Laboratorio | Administrador de Laboratorio |
| Cerrar la reserva | ejercitado | Administrador de Laboratorio | Administrador de Laboratorio |
| Comprobar cantidad y disponibilidad antes de confirmar | ejercitado | Estudiante, Profesor, Técnico de Laboratorio, Asistente de laboratorio, Administrador de Laboratorio, Administrativo de centro de trabajo | Administrador de Laboratorio |

### `RES-02` — Iniciar y expirar reservas automáticamente

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Marcar como prestado al llegar la fecha de inicio | fuera del alcance de la sonda | Sistema | — |
| Denegar la reserva que expira sin stock | fuera del alcance de la sonda | Sistema | — |

### `RISK-01` — Definir las zonas de riesgo de la organización

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Listar y abrir el detalle de una zona de riesgo | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio | — |
| Crear una zona de riesgo y su tipo | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio | — |
| Editar o borrar una zona | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio | — |
| Ver el panel de zonas y su reporte | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio | — |
| Consultar las jornadas de trabajo de la zona | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio | — |

### `RISK-02` — Reportar y dar seguimiento a un incidente

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Registrar un incidente | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio, Estudiante, Profesor | — |
| Listar incidentes y abrir su detalle | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio | — |
| Corregir o eliminar un incidente | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio | — |
| Descargar el reporte de incidentes | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio | — |

### `RISK-03` — Mantener edificios, estructuras y regentes

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Listar, crear y editar edificios | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio | — |
| Listar, crear y editar estructuras | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio | — |
| Consultar los regentes del laboratorio | solo superusuario | Administrativo superior, Administrador de Laboratorio, Regente, Asistente de laboratorio, Solo Lectura, Técnico de Laboratorio | — |

### `IPER-01` — Solicitar, llenar y auditar una evaluación IPER

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Solicitar a los laboratorios de una zona que llenen su IPER | nunca ejercitado | Administrador IPER, Administrativo superior | — |
| Crear la evaluación del laboratorio | solo superusuario | Administrador de Laboratorio, Regente asignado al laboratorio, Administrador IPER | — |
| Identificar peligros y valorar el riesgo | solo superusuario | Administrador de Laboratorio, Regente asignado al laboratorio, Administrador IPER | — |
| Marcar la evaluación como completada (o devolverla a borrador) | nunca ejercitado | Administrador de Laboratorio, Regente asignado al laboratorio, Administrador IPER | — |
| Clonar la evaluación para actualizarla | solo superusuario | Administrador de Laboratorio, Regente asignado al laboratorio, Administrador IPER | — |
| Observar la evaluación sin poder modificarla | nunca ejercitado | Auditor IPER | — |
| Listar evaluaciones, ver el detalle y su histórico | solo superusuario | Auditor IPER, Administrador IPER, Administrador de Laboratorio, Regente, Solo Lectura | — |
| Ver el panel consolidado de IPER | solo superusuario | Administrador IPER, Administrativo superior, Auditor IPER | — |
| Alternar el anonimato de la evaluación | nunca ejercitado | Administrador de Laboratorio, Administrador IPER | — |
| Mantener el catálogo IPER de la organización raíz | nunca ejercitado | Administrador IPER | — |
| Eliminar una evaluación | nunca ejercitado | Administrador IPER, Administrativo superior | — |

### `IPER-02` — Recordar por correo las evaluaciones IPER que toca actualizar

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Enviar los recordatorios de actualización | fuera del alcance de la sonda | Sistema | — |

### `RISK-04` — Generar la bitácora diaria de establecimientos

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Crear los reportes de establecimiento | fuera del alcance de la sonda | Sistema | — |

### `SGA-01` — Registrar una sustancia y llevarla hasta su aprobación

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Abrir el asistente y describir la sustancia (paso 1) | solo superusuario | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Lectura y agregado de sustancias, Manejo de sustancias del laboratorio | — |
| Completar la hoja de seguridad (paso 4) | solo superusuario | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Lectura y agregado de sustancias, Manejo de sustancias del laboratorio | — |
| Subir la ficha de datos de seguridad y seguir la extracción | solo superusuario | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Lectura y agregado de sustancias, Manejo de sustancias del laboratorio | — |
| Añadir el proveedor de la sustancia | solo superusuario | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Lectura y agregado de sustancias, Manejo de sustancias del laboratorio | — |
| Enviar la sustancia a revisión | solo superusuario | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Lectura y agregado de sustancias, Manejo de sustancias del laboratorio | — |
| Ver la bandeja de sustancias por aprobar | solo superusuario | Administrativo superior, SGA, Organization Management | — |
| Dejar, editar o borrar observaciones sobre la sustancia | solo superusuario | Administrativo superior, SGA, Organization Management, Administrador de Laboratorio | — |
| Abrir el detalle de la sustancia en revisión | solo superusuario | Administrativo superior, SGA, Organization Management | — |
| Aprobar la sustancia | solo superusuario | Administrativo superior, SGA, Organization Management | — |
| Eliminar la sustancia | solo superusuario | Administrativo superior, SGA, Organization Management, Administrador de Laboratorio | — |

### `SGA-02` — Obtener la etiqueta GHS y la ficha de seguridad de una sustancia

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Generar la etiqueta de la sustancia | solo superusuario | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Regente, Solo Lectura, Estudiante | — |
| Descargar la hoja de seguridad en PDF | nunca ejercitado | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Regente, Solo Lectura, Estudiante | — |
| Consultar los complementos SGA de una sustancia | nunca ejercitado | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Regente, Solo Lectura, Estudiante | — |

### `SGA-03` — Mantener el catálogo de clasificación GHS

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Consultar frases H, frases P y palabras de advertencia | solo superusuario | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Regente, Solo Lectura, Estudiante | — |
| Dar de alta una frase o palabra de advertencia | solo superusuario | SGA, Administrativo superior | — |
| Editar una frase o palabra de advertencia | solo superusuario | SGA, Administrativo superior | — |
| Consultar sustancias peligrosas y sus categorías | solo superusuario | SGA, Administrador de Laboratorio, Técnico de Laboratorio, Regente, Solo Lectura, Estudiante | — |

### `SGA-04` — Diseñar plantillas de etiqueta en el editor SGA

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Abrir el editor de plantillas | solo superusuario | SGA, Administrativo superior, Administrador de Laboratorio | — |
| Crear una plantilla personal | solo superusuario | SGA, Administrativo superior, Administrador de Laboratorio | — |
| Editar la plantilla paso a paso | solo superusuario | SGA, Administrativo superior, Administrador de Laboratorio | — |
| Previsualizar la etiqueta y su código de barras | solo superusuario | SGA, Administrativo superior, Administrador de Laboratorio | — |
| Borrar una plantilla | nunca ejercitado | SGA, Administrativo superior | — |

### `SGA-05` — Gestionar empresas y tamaños de recipiente del etiquetado

| Paso | Estado | Roles declarados | Roles observados |
|---|---|---|---|
| Listar y consultar empresas | solo superusuario | SGA, Administrativo superior, Administrador de Laboratorio | — |
| Crear o editar una empresa | solo superusuario | SGA, Administrativo superior | — |
| Quitar una empresa | solo superusuario | SGA, Administrativo superior | — |
| Consultar y dar de alta tamaños de recipiente | solo superusuario | SGA, Administrativo superior, Administrador de Laboratorio, Depositante de residuos | — |

## Lo que falta probar

Cada línea es un par (paso, rol) que el catálogo declara y la sonda no vio nunca: una prueba que falta, con su escenario ya escrito.

| Funcionalidad | Paso | Rol sin ejercitar | Estado del paso |
|---|---|---|---|
| `ACAD-01` | Crear la plantilla del procedimiento | Profesor | solo superusuario |
| `ACAD-01` | Crear la plantilla del procedimiento | Administrador de Laboratorio | solo superusuario |
| `ACAD-01` | Crear la plantilla del procedimiento | Asistente de laboratorio | solo superusuario |
| `ACAD-01` | Listar y consultar plantillas | Profesor | solo superusuario |
| `ACAD-01` | Listar y consultar plantillas | Administrador de Laboratorio | solo superusuario |
| `ACAD-01` | Listar y consultar plantillas | Asistente de laboratorio | solo superusuario |
| `ACAD-01` | Listar y consultar plantillas | Estudiante | solo superusuario |
| `ACAD-01` | Listar y consultar plantillas | Solo Lectura | solo superusuario |
| `ACAD-01` | Editar la plantilla | Profesor | solo superusuario |
| `ACAD-01` | Editar la plantilla | Administrador de Laboratorio | solo superusuario |
| `ACAD-01` | Editar la plantilla | Asistente de laboratorio | solo superusuario |
| `ACAD-01` | Añadir pasos a la plantilla | Profesor | solo superusuario |
| `ACAD-01` | Añadir pasos a la plantilla | Administrador de Laboratorio | solo superusuario |
| `ACAD-01` | Añadir pasos a la plantilla | Asistente de laboratorio | solo superusuario |
| `ACAD-01` | Editar un paso | Profesor | solo superusuario |
| `ACAD-01` | Editar un paso | Administrador de Laboratorio | solo superusuario |
| `ACAD-01` | Editar un paso | Asistente de laboratorio | solo superusuario |
| `ACAD-01` | Borrar un paso o la plantilla completa | Profesor | solo superusuario |
| `ACAD-01` | Borrar un paso o la plantilla completa | Administrador de Laboratorio | solo superusuario |
| `ACAD-01` | Borrar un paso o la plantilla completa | Asistente de laboratorio | solo superusuario |
| `ACAD-02` | Crear mi procedimiento a partir de una plantilla | Estudiante | solo superusuario |
| `ACAD-02` | Crear mi procedimiento a partir de una plantilla | Profesor | solo superusuario |
| `ACAD-02` | Crear mi procedimiento a partir de una plantilla | Técnico de Laboratorio | solo superusuario |
| `ACAD-02` | Crear mi procedimiento a partir de una plantilla | Asistente de laboratorio | solo superusuario |
| `ACAD-02` | Ver mis procedimientos | Estudiante | ejercitado |
| `ACAD-02` | Ver mis procedimientos | Técnico de Laboratorio | ejercitado |
| `ACAD-02` | Ver mis procedimientos | Asistente de laboratorio | ejercitado |
| `ACAD-02` | Generar la reserva de todo el material del procedimiento | Estudiante | solo superusuario |
| `ACAD-02` | Generar la reserva de todo el material del procedimiento | Profesor | solo superusuario |
| `ACAD-02` | Generar la reserva de todo el material del procedimiento | Técnico de Laboratorio | solo superusuario |
| `ACAD-02` | Generar la reserva de todo el material del procedimiento | Asistente de laboratorio | solo superusuario |
| `ACAD-02` | Completar los pasos y cambiar el estado | Estudiante | solo superusuario |
| `ACAD-02` | Completar los pasos y cambiar el estado | Profesor | solo superusuario |
| `ACAD-02` | Completar los pasos y cambiar el estado | Técnico de Laboratorio | solo superusuario |
| `ACAD-02` | Completar los pasos y cambiar el estado | Asistente de laboratorio | solo superusuario |
| `ACAD-02` | Quitar mi procedimiento | Estudiante | solo superusuario |
| `ACAD-02` | Quitar mi procedimiento | Profesor | solo superusuario |
| `ACAD-02` | Quitar mi procedimiento | Técnico de Laboratorio | solo superusuario |
| `ACAD-02` | Quitar mi procedimiento | Asistente de laboratorio | solo superusuario |
| `ORG-01` | Elegir la organización con la que se trabaja | Estudiante | solo superusuario |
| `ORG-01` | Elegir la organización con la que se trabaja | Profesor | solo superusuario |
| `ORG-01` | Elegir la organización con la que se trabaja | Técnico de Laboratorio | solo superusuario |
| `ORG-01` | Elegir la organización con la que se trabaja | Administrador de Laboratorio | solo superusuario |
| `ORG-01` | Elegir la organización con la que se trabaja | Administrativo superior | solo superusuario |
| `ORG-01` | Elegir la organización con la que se trabaja | Regente | solo superusuario |
| `ORG-01` | Elegir la organización con la que se trabaja | Solo Lectura | solo superusuario |
| `ORG-01` | Ver el mapa de laboratorios | Administrador de Laboratorio | solo superusuario |
| `ORG-01` | Ver el mapa de laboratorios | Administrativo superior | solo superusuario |
| `ORG-01` | Ver el mapa de laboratorios | Regente | solo superusuario |
| `ORG-01` | Listar organizaciones y sus laboratorios | Administrativo superior | solo superusuario |
| `ORG-01` | Listar organizaciones y sus laboratorios | Organization Management | solo superusuario |
| `ORG-01` | Listar organizaciones y sus laboratorios | Administrador de Laboratorio | solo superusuario |
| `ORG-01` | Listar organizaciones y sus laboratorios | Administrativo de centro de trabajo | solo superusuario |
| `ORG-02` | Abrir el gestor de la organización | Administrativo superior | solo superusuario |
| `ORG-02` | Abrir el gestor de la organización | Organization Management | solo superusuario |
| `ORG-02` | Abrir el gestor de la organización | Administrador de Laboratorio | solo superusuario |
| `ORG-02` | Abrir el gestor de la organización | Administrativo de centro de trabajo | solo superusuario |
| `ORG-02` | Añadir usuarios a la organización | Administrativo superior | solo superusuario |
| `ORG-02` | Añadir usuarios a la organización | Organization Management | solo superusuario |
| `ORG-02` | Añadir usuarios a la organización | Administrador de Laboratorio | solo superusuario |
| `ORG-02` | Añadir usuarios a la organización | Administrativo de centro de trabajo | solo superusuario |
| `ORG-02` | Consultar, crear y editar los roles de la organización | Administrativo superior | solo superusuario |
| `ORG-02` | Consultar, crear y editar los roles de la organización | Organization Management | solo superusuario |
| `ORG-02` | Consultar, crear y editar los roles de la organización | Administrador de Laboratorio | solo superusuario |
| `ORG-02` | Consultar, crear y editar los roles de la organización | Administrativo de centro de trabajo | solo superusuario |
| `ORG-02` | Quitar un rol de la organización | Administrativo superior | solo superusuario |
| `ORG-02` | Quitar un rol de la organización | Organization Management | solo superusuario |
| `ORG-02` | Quitar un rol de la organización | Administrador de Laboratorio | solo superusuario |
| `ORG-02` | Quitar un rol de la organización | Administrativo de centro de trabajo | solo superusuario |
| `ORG-02` | Copiar el juego de roles a otra organización | Administrativo superior | solo superusuario |
| `ORG-02` | Copiar el juego de roles a otra organización | Organization Management | solo superusuario |
| `ORG-02` | Copiar el juego de roles a otra organización | Administrador de Laboratorio | solo superusuario |
| `ORG-02` | Copiar el juego de roles a otra organización | Administrativo de centro de trabajo | solo superusuario |
| `ORG-02` | Habilitar organizaciones hijas y relacionar modelos | Administrativo superior | solo superusuario |
| `ORG-02` | Habilitar organizaciones hijas y relacionar modelos | Organization Management | solo superusuario |
| `ORG-02` | Habilitar organizaciones hijas y relacionar modelos | Administrador de Laboratorio | solo superusuario |
| `ORG-02` | Habilitar organizaciones hijas y relacionar modelos | Administrativo de centro de trabajo | solo superusuario |
| `ORG-02` | Consultar quién administra la organización | Administrativo superior | nunca ejercitado |
| `ORG-02` | Consultar quién administra la organización | Organization Management | nunca ejercitado |
| `ORG-02` | Consultar quién administra la organización | Administrador de Laboratorio | nunca ejercitado |
| `ORG-02` | Consultar quién administra la organización | Administrativo de centro de trabajo | nunca ejercitado |
| `ORG-03` | Autenticarse con la firma digital del BCCR | Anónimo | nunca ejercitado |
| `ORG-03` | Obtener el QR del segundo factor | Estudiante | nunca ejercitado |
| `ORG-03` | Obtener el QR del segundo factor | Profesor | nunca ejercitado |
| `ORG-03` | Obtener el QR del segundo factor | Administrador de Laboratorio | nunca ejercitado |
| `ORG-04` | Entrar como otro usuario | Administrativo superior | nunca ejercitado |
| `ORG-04` | Entrar como otro usuario | Organization Management | nunca ejercitado |
| `ORG-04` | Volver a la identidad propia | Administrativo superior | nunca ejercitado |
| `ORG-04` | Volver a la identidad propia | Organization Management | nunca ejercitado |
| `INV-01` | Listar sustancias, materiales y equipos | Administrador de Laboratorio | solo superusuario |
| `INV-01` | Listar sustancias, materiales y equipos | Técnico de Laboratorio | solo superusuario |
| `INV-01` | Listar sustancias, materiales y equipos | Asistente de laboratorio | solo superusuario |
| `INV-01` | Listar sustancias, materiales y equipos | Lectura y agregado de sustancias | solo superusuario |
| `INV-01` | Listar sustancias, materiales y equipos | Estudiante | solo superusuario |
| `INV-01` | Listar sustancias, materiales y equipos | Profesor | solo superusuario |
| `INV-01` | Listar sustancias, materiales y equipos | Regente | solo superusuario |
| `INV-01` | Listar sustancias, materiales y equipos | Solo Lectura | solo superusuario |
| `INV-01` | Listar sustancias, materiales y equipos | Administrativo superior | solo superusuario |
| `INV-01` | Dar de alta un objeto en el catálogo | Administrador de Laboratorio | solo superusuario |
| `INV-01` | Dar de alta un objeto en el catálogo | Técnico de Laboratorio | solo superusuario |
| `INV-01` | Dar de alta un objeto en el catálogo | Asistente de laboratorio | solo superusuario |
| `INV-01` | Dar de alta un objeto en el catálogo | Lectura y agregado de sustancias | solo superusuario |
| `INV-01` | Editar o borrar un objeto del catálogo | Administrador de Laboratorio | solo superusuario |
| `INV-01` | Editar o borrar un objeto del catálogo | Técnico de Laboratorio | solo superusuario |
| `INV-01` | Editar o borrar un objeto del catálogo | Asistente de laboratorio | solo superusuario |
| `INV-01` | Editar o borrar un objeto del catálogo | Lectura y agregado de sustancias | solo superusuario |
| `INV-01` | Consultar los rasgos de los objetos | Administrador de Laboratorio | solo superusuario |
| `INV-01` | Consultar los rasgos de los objetos | Técnico de Laboratorio | solo superusuario |
| `INV-01` | Consultar los rasgos de los objetos | Asistente de laboratorio | solo superusuario |
| `INV-01` | Consultar los rasgos de los objetos | Lectura y agregado de sustancias | solo superusuario |
| `INV-01` | Consultar los rasgos de los objetos | Estudiante | solo superusuario |
| `INV-01` | Consultar los rasgos de los objetos | Profesor | solo superusuario |
| `INV-01` | Consultar los rasgos de los objetos | Regente | solo superusuario |
| `INV-01` | Consultar los rasgos de los objetos | Solo Lectura | solo superusuario |
| `INV-01` | Consultar los rasgos de los objetos | Administrativo superior | solo superusuario |
| `INV-01` | Consultar los proveedores | Administrador de Laboratorio | solo superusuario |
| `INV-01` | Consultar los proveedores | Técnico de Laboratorio | solo superusuario |
| `INV-01` | Consultar los proveedores | Asistente de laboratorio | solo superusuario |
| `INV-01` | Consultar los proveedores | Lectura y agregado de sustancias | solo superusuario |
| `INV-01` | Consultar los proveedores | Estudiante | solo superusuario |
| `INV-01` | Consultar los proveedores | Profesor | solo superusuario |
| `INV-01` | Consultar los proveedores | Regente | solo superusuario |
| `INV-01` | Consultar los proveedores | Solo Lectura | solo superusuario |
| `INV-01` | Consultar los proveedores | Administrativo superior | solo superusuario |
| `INV-02` | Ver los objetos de un estante | Administrador de Laboratorio | nunca ejercitado |
| `INV-02` | Ver los objetos de un estante | Técnico de Laboratorio | nunca ejercitado |
| `INV-02` | Ver los objetos de un estante | Asistente de laboratorio | nunca ejercitado |
| `INV-02` | Ver los objetos de un estante | Lectura y agregado de sustancias | nunca ejercitado |
| `INV-02` | Ver los objetos de un estante | Estudiante | nunca ejercitado |
| `INV-02` | Ver los objetos de un estante | Profesor | nunca ejercitado |
| `INV-02` | Ver los objetos de un estante | Regente | nunca ejercitado |
| `INV-02` | Ver los objetos de un estante | Solo Lectura | nunca ejercitado |
| `INV-02` | Ver los objetos de un estante | Administrativo superior | nunca ejercitado |
| `INV-02` | Colocar un objeto en el estante | Administrador de Laboratorio | nunca ejercitado |
| `INV-02` | Colocar un objeto en el estante | Técnico de Laboratorio | nunca ejercitado |
| `INV-02` | Colocar un objeto en el estante | Asistente de laboratorio | nunca ejercitado |
| `INV-02` | Colocar un objeto en el estante | Lectura y agregado de sustancias | nunca ejercitado |
| `INV-02` | Colocar un objeto en el estante | Estudiante | nunca ejercitado |
| `INV-02` | Colocar un objeto en el estante | Depositante de residuos | nunca ejercitado |
| `INV-02` | Abrir el detalle del objeto, con su QR | Administrador de Laboratorio | solo superusuario |
| `INV-02` | Abrir el detalle del objeto, con su QR | Técnico de Laboratorio | solo superusuario |
| `INV-02` | Abrir el detalle del objeto, con su QR | Asistente de laboratorio | solo superusuario |
| `INV-02` | Abrir el detalle del objeto, con su QR | Lectura y agregado de sustancias | solo superusuario |
| `INV-02` | Abrir el detalle del objeto, con su QR | Estudiante | solo superusuario |
| `INV-02` | Abrir el detalle del objeto, con su QR | Profesor | solo superusuario |
| `INV-02` | Abrir el detalle del objeto, con su QR | Regente | solo superusuario |
| `INV-02` | Abrir el detalle del objeto, con su QR | Solo Lectura | solo superusuario |
| `INV-02` | Abrir el detalle del objeto, con su QR | Administrativo superior | solo superusuario |
| `INV-02` | Editar la cantidad, el límite y los datos del objeto | Administrador de Laboratorio | solo superusuario |
| `INV-02` | Editar la cantidad, el límite y los datos del objeto | Técnico de Laboratorio | solo superusuario |
| `INV-02` | Editar la cantidad, el límite y los datos del objeto | Asistente de laboratorio | solo superusuario |
| `INV-02` | Editar la cantidad, el límite y los datos del objeto | Lectura y agregado de sustancias | solo superusuario |
| `INV-02` | Editar la cantidad, el límite y los datos del objeto | Estudiante | solo superusuario |
| `INV-02` | Generar la etiqueta del objeto | Administrador de Laboratorio | nunca ejercitado |
| `INV-02` | Generar la etiqueta del objeto | Técnico de Laboratorio | nunca ejercitado |
| `INV-02` | Generar la etiqueta del objeto | Asistente de laboratorio | nunca ejercitado |
| `INV-02` | Generar la etiqueta del objeto | Lectura y agregado de sustancias | nunca ejercitado |
| `INV-02` | Generar la etiqueta del objeto | Estudiante | nunca ejercitado |
| `INV-02` | Generar la etiqueta del objeto | Profesor | nunca ejercitado |
| `INV-02` | Generar la etiqueta del objeto | Regente | nunca ejercitado |
| `INV-02` | Generar la etiqueta del objeto | Solo Lectura | nunca ejercitado |
| `INV-02` | Generar la etiqueta del objeto | Administrativo superior | nunca ejercitado |
| `INV-02` | Borrar o desechar el objeto | Administrador de Laboratorio | solo superusuario |
| `INV-02` | Borrar o desechar el objeto | Técnico de Laboratorio | solo superusuario |
| `INV-02` | Borrar o desechar el objeto | Asistente de laboratorio | solo superusuario |
| `INV-02` | Borrar o desechar el objeto | Lectura y agregado de sustancias | solo superusuario |
| `INV-02` | Borrar o desechar el objeto | Depositante de residuos | solo superusuario |
| `INV-02` | Borrar o desechar el objeto | Tesista modulo desechos | solo superusuario |
| `INV-02` | Ver los reactivos del estante y su reorden | Administrador de Laboratorio | solo superusuario |
| `INV-02` | Ver los reactivos del estante y su reorden | Técnico de Laboratorio | solo superusuario |
| `INV-02` | Ver los reactivos del estante y su reorden | Asistente de laboratorio | solo superusuario |
| `INV-02` | Ver los reactivos del estante y su reorden | Lectura y agregado de sustancias | solo superusuario |
| `INV-03` | Subir el fichero y previsualizar | Administrador de Laboratorio | solo superusuario |
| `INV-03` | Subir el fichero y previsualizar | Técnico de Laboratorio | solo superusuario |
| `INV-03` | Subir el fichero y previsualizar | Asistente de laboratorio | solo superusuario |
| `INV-03` | Subir el fichero y previsualizar | Lectura y agregado de sustancias | solo superusuario |
| `INV-03` | Confirmar y crear los objetos en el estante | Administrador de Laboratorio | nunca ejercitado |
| `INV-03` | Confirmar y crear los objetos en el estante | Técnico de Laboratorio | nunca ejercitado |
| `INV-03` | Confirmar y crear los objetos en el estante | Asistente de laboratorio | nunca ejercitado |
| `INV-03` | Confirmar y crear los objetos en el estante | Lectura y agregado de sustancias | nunca ejercitado |
| `INV-04` | Ver el panel de existencias de reactivos | Administrador de Laboratorio | solo superusuario |
| `INV-04` | Ver el panel de existencias de reactivos | Técnico de Laboratorio | solo superusuario |
| `INV-04` | Ver el panel de existencias de reactivos | Asistente de laboratorio | solo superusuario |
| `INV-04` | Ver el panel de existencias de reactivos | Lectura y agregado de sustancias | solo superusuario |
| `INV-04` | Ver el panel de existencias de reactivos | Regente | solo superusuario |
| `INV-04` | Silenciar los avisos de un objeto | Administrador de Laboratorio | solo superusuario |
| `INV-04` | Silenciar los avisos de un objeto | Técnico de Laboratorio | solo superusuario |
| `INV-04` | Silenciar los avisos de un objeto | Asistente de laboratorio | solo superusuario |
| `INV-04` | Silenciar los avisos de un objeto | Lectura y agregado de sustancias | solo superusuario |
| `INV-06` | Programar el periodo de los informes | Administrador de Laboratorio | solo superusuario |
| `INV-06` | Programar el periodo de los informes | Asistente de laboratorio | solo superusuario |
| `INV-06` | Crear el informe | Administrador de Laboratorio | solo superusuario |
| `INV-06` | Crear el informe | Asistente de laboratorio | solo superusuario |
| `INV-06` | Crear el informe | Técnico de Laboratorio | solo superusuario |
| `INV-06` | Completar el informe y cambiar su estado | Administrador de Laboratorio | solo superusuario |
| `INV-06` | Retirar un informe | Administrador de Laboratorio | solo superusuario |
| `INV-07` | Abrir el índice de reportes del laboratorio | Administrador de Laboratorio | solo superusuario |
| `INV-07` | Abrir el índice de reportes del laboratorio | Técnico de Laboratorio | solo superusuario |
| `INV-07` | Abrir el índice de reportes del laboratorio | Asistente de laboratorio | solo superusuario |
| `INV-07` | Abrir el índice de reportes del laboratorio | Lectura y agregado de sustancias | solo superusuario |
| `INV-07` | Abrir el índice de reportes del laboratorio | Estudiante | solo superusuario |
| `INV-07` | Abrir el índice de reportes del laboratorio | Profesor | solo superusuario |
| `INV-07` | Abrir el índice de reportes del laboratorio | Regente | solo superusuario |
| `INV-07` | Abrir el índice de reportes del laboratorio | Solo Lectura | solo superusuario |
| `INV-07` | Abrir el índice de reportes del laboratorio | Administrativo superior | solo superusuario |
| `INV-07` | Consultar y descargar los reportes de códigos H | Administrador de Laboratorio | solo superusuario |
| `INV-07` | Consultar y descargar los reportes de códigos H | Técnico de Laboratorio | solo superusuario |
| `INV-07` | Consultar y descargar los reportes de códigos H | Asistente de laboratorio | solo superusuario |
| `INV-07` | Consultar y descargar los reportes de códigos H | Lectura y agregado de sustancias | solo superusuario |
| `INV-07` | Consultar y descargar los reportes de códigos H | Estudiante | solo superusuario |
| `INV-07` | Consultar y descargar los reportes de códigos H | Profesor | solo superusuario |
| `INV-07` | Consultar y descargar los reportes de códigos H | Regente | solo superusuario |
| `INV-07` | Consultar y descargar los reportes de códigos H | Solo Lectura | solo superusuario |
| `INV-07` | Consultar y descargar los reportes de códigos H | Administrativo superior | solo superusuario |
| `INV-07` | Descargar el reporte de objetos en estantes | Administrador de Laboratorio | solo superusuario |
| `INV-07` | Descargar el reporte de objetos en estantes | Técnico de Laboratorio | solo superusuario |
| `INV-07` | Descargar el reporte de objetos en estantes | Asistente de laboratorio | solo superusuario |
| `INV-07` | Descargar el reporte de objetos en estantes | Lectura y agregado de sustancias | solo superusuario |
| `INV-07` | Descargar el reporte de objetos en estantes | Estudiante | solo superusuario |
| `INV-07` | Descargar el reporte de objetos en estantes | Profesor | solo superusuario |
| `INV-07` | Descargar el reporte de objetos en estantes | Regente | solo superusuario |
| `INV-07` | Descargar el reporte de objetos en estantes | Solo Lectura | solo superusuario |
| `INV-07` | Descargar el reporte de objetos en estantes | Administrativo superior | solo superusuario |
| `INV-07` | Ver la cobertura de fichas de seguridad | Administrador de Laboratorio | solo superusuario |
| `INV-07` | Ver la cobertura de fichas de seguridad | Técnico de Laboratorio | solo superusuario |
| `INV-07` | Ver la cobertura de fichas de seguridad | Asistente de laboratorio | solo superusuario |
| `INV-07` | Ver la cobertura de fichas de seguridad | Lectura y agregado de sustancias | solo superusuario |
| `INV-07` | Ver la cobertura de fichas de seguridad | Estudiante | solo superusuario |
| `INV-07` | Ver la cobertura de fichas de seguridad | Profesor | solo superusuario |
| `INV-07` | Ver la cobertura de fichas de seguridad | Regente | solo superusuario |
| `INV-07` | Ver la cobertura de fichas de seguridad | Solo Lectura | solo superusuario |
| `INV-07` | Ver la cobertura de fichas de seguridad | Administrativo superior | solo superusuario |
| `INV-08` | Listar protocolos | Administrador de Laboratorio | solo superusuario |
| `INV-08` | Listar protocolos | Técnico de Laboratorio | solo superusuario |
| `INV-08` | Listar protocolos | Asistente de laboratorio | solo superusuario |
| `INV-08` | Listar protocolos | Lectura y agregado de sustancias | solo superusuario |
| `INV-08` | Listar protocolos | Estudiante | solo superusuario |
| `INV-08` | Listar protocolos | Profesor | solo superusuario |
| `INV-08` | Listar protocolos | Regente | solo superusuario |
| `INV-08` | Listar protocolos | Solo Lectura | solo superusuario |
| `INV-08` | Listar protocolos | Administrativo superior | solo superusuario |
| `INV-08` | Crear o editar un protocolo | Administrador de Laboratorio | solo superusuario |
| `INV-08` | Crear o editar un protocolo | Técnico de Laboratorio | solo superusuario |
| `INV-08` | Crear o editar un protocolo | Asistente de laboratorio | solo superusuario |
| `INV-08` | Crear o editar un protocolo | Lectura y agregado de sustancias | solo superusuario |
| `INV-08` | Borrar un protocolo (va a la papelera) | Administrador de Laboratorio | solo superusuario |
| `INV-08` | Borrar un protocolo (va a la papelera) | Técnico de Laboratorio | solo superusuario |
| `INV-08` | Borrar un protocolo (va a la papelera) | Asistente de laboratorio | solo superusuario |
| `INV-08` | Borrar un protocolo (va a la papelera) | Lectura y agregado de sustancias | solo superusuario |
| `LAB-01` | Crear la organización | Administrativo superior | solo superusuario |
| `LAB-01` | Crear la organización | Organization Management | solo superusuario |
| `LAB-01` | Editar la organización y sus acciones | Administrativo superior | solo superusuario |
| `LAB-01` | Editar la organización y sus acciones | Organization Management | solo superusuario |
| `LAB-01` | Borrar la organización | Administrativo superior | solo superusuario |
| `LAB-01` | Borrar la organización | Organization Management | solo superusuario |
| `LAB-02` | Pedir un laboratorio nuevo o una organización nueva | Técnico de Laboratorio | solo superusuario |
| `LAB-02` | Pedir un laboratorio nuevo o una organización nueva | Profesor | solo superusuario |
| `LAB-02` | Pedir un laboratorio nuevo o una organización nueva | Asistente de laboratorio | solo superusuario |
| `LAB-02` | Pedir un laboratorio nuevo o una organización nueva | Administrador de Laboratorio | solo superusuario |
| `LAB-02` | Revisar la solicitud y aprobarla o rechazarla | Administrativo superior | solo superusuario |
| `LAB-03` | Crear el laboratorio | Administrativo superior | solo superusuario |
| `LAB-03` | Crear el laboratorio | Administrador de Laboratorio | solo superusuario |
| `LAB-03` | Crear el laboratorio | Creador de laboratorio | solo superusuario |
| `LAB-03` | Crear el laboratorio | Asistente de laboratorio | solo superusuario |
| `LAB-03` | Ver mis laboratorios y entrar en uno | Administrativo superior | ejercitado |
| `LAB-03` | Ver mis laboratorios y entrar en uno | Creador de laboratorio | ejercitado |
| `LAB-03` | Ver mis laboratorios y entrar en uno | Asistente de laboratorio | ejercitado |
| `LAB-03` | Ver mis laboratorios y entrar en uno | Técnico de Laboratorio | ejercitado |
| `LAB-03` | Ver mis laboratorios y entrar en uno | Profesor | ejercitado |
| `LAB-03` | Ver mis laboratorios y entrar en uno | Regente | ejercitado |
| `LAB-03` | Ver mis laboratorios y entrar en uno | Solo Lectura | ejercitado |
| `LAB-03` | Abrir la vista del laboratorio con su árbol de salas y estantes | Administrativo superior | solo superusuario |
| `LAB-03` | Abrir la vista del laboratorio con su árbol de salas y estantes | Administrador de Laboratorio | solo superusuario |
| `LAB-03` | Abrir la vista del laboratorio con su árbol de salas y estantes | Creador de laboratorio | solo superusuario |
| `LAB-03` | Abrir la vista del laboratorio con su árbol de salas y estantes | Asistente de laboratorio | solo superusuario |
| `LAB-03` | Abrir la vista del laboratorio con su árbol de salas y estantes | Técnico de Laboratorio | solo superusuario |
| `LAB-03` | Abrir la vista del laboratorio con su árbol de salas y estantes | Estudiante | solo superusuario |
| `LAB-03` | Abrir la vista del laboratorio con su árbol de salas y estantes | Profesor | solo superusuario |
| `LAB-03` | Abrir la vista del laboratorio con su árbol de salas y estantes | Regente | solo superusuario |
| `LAB-03` | Abrir la vista del laboratorio con su árbol de salas y estantes | Solo Lectura | solo superusuario |
| `LAB-03` | Editar o borrar el laboratorio | Administrativo superior | solo superusuario |
| `LAB-03` | Editar o borrar el laboratorio | Administrador de Laboratorio | solo superusuario |
| `LAB-03` | Editar o borrar el laboratorio | Creador de laboratorio | solo superusuario |
| `LAB-03` | Editar o borrar el laboratorio | Asistente de laboratorio | solo superusuario |
| `LAB-03` | Consultar los procesos del laboratorio | Administrativo superior | solo superusuario |
| `LAB-03` | Consultar los procesos del laboratorio | Administrador de Laboratorio | solo superusuario |
| `LAB-03` | Consultar los procesos del laboratorio | Creador de laboratorio | solo superusuario |
| `LAB-03` | Consultar los procesos del laboratorio | Asistente de laboratorio | solo superusuario |
| `LAB-03` | Consultar los procesos del laboratorio | Técnico de Laboratorio | solo superusuario |
| `LAB-03` | Consultar los procesos del laboratorio | Estudiante | solo superusuario |
| `LAB-03` | Consultar los procesos del laboratorio | Profesor | solo superusuario |
| `LAB-03` | Consultar los procesos del laboratorio | Regente | solo superusuario |
| `LAB-03` | Consultar los procesos del laboratorio | Solo Lectura | solo superusuario |
| `LAB-04` | Listar, crear, editar y borrar salas | Administrativo superior | solo superusuario |
| `LAB-04` | Listar, crear, editar y borrar salas | Administrador de Laboratorio | solo superusuario |
| `LAB-04` | Listar, crear, editar y borrar salas | Creador de laboratorio | solo superusuario |
| `LAB-04` | Listar, crear, editar y borrar salas | Asistente de laboratorio | solo superusuario |
| `LAB-04` | Regenerar el QR de la sala | Administrativo superior | solo superusuario |
| `LAB-04` | Regenerar el QR de la sala | Administrador de Laboratorio | solo superusuario |
| `LAB-04` | Regenerar el QR de la sala | Creador de laboratorio | solo superusuario |
| `LAB-04` | Regenerar el QR de la sala | Asistente de laboratorio | solo superusuario |
| `LAB-04` | Listar, crear, editar y borrar muebles | Administrativo superior | solo superusuario |
| `LAB-04` | Listar, crear, editar y borrar muebles | Administrador de Laboratorio | solo superusuario |
| `LAB-04` | Listar, crear, editar y borrar muebles | Creador de laboratorio | solo superusuario |
| `LAB-04` | Listar, crear, editar y borrar muebles | Asistente de laboratorio | solo superusuario |
| `LAB-04` | Crear, editar y borrar estantes | Administrativo superior | solo superusuario |
| `LAB-04` | Crear, editar y borrar estantes | Administrador de Laboratorio | solo superusuario |
| `LAB-04` | Crear, editar y borrar estantes | Creador de laboratorio | solo superusuario |
| `LAB-04` | Crear, editar y borrar estantes | Asistente de laboratorio | solo superusuario |
| `LAB-04` | Ver los contenedores de un estante | Administrativo superior | solo superusuario |
| `LAB-04` | Ver los contenedores de un estante | Administrador de Laboratorio | solo superusuario |
| `LAB-04` | Ver los contenedores de un estante | Creador de laboratorio | solo superusuario |
| `LAB-04` | Ver los contenedores de un estante | Asistente de laboratorio | solo superusuario |
| `LAB-04` | Ver los contenedores de un estante | Técnico de Laboratorio | solo superusuario |
| `LAB-04` | Ver los contenedores de un estante | Estudiante | solo superusuario |
| `LAB-04` | Ver los contenedores de un estante | Profesor | solo superusuario |
| `LAB-04` | Ver los contenedores de un estante | Regente | solo superusuario |
| `LAB-04` | Ver los contenedores de un estante | Solo Lectura | solo superusuario |
| `LAB-04` | Descargar el reporte de la sala | Administrativo superior | solo superusuario |
| `LAB-04` | Descargar el reporte de la sala | Administrador de Laboratorio | solo superusuario |
| `LAB-04` | Descargar el reporte de la sala | Creador de laboratorio | solo superusuario |
| `LAB-04` | Descargar el reporte de la sala | Asistente de laboratorio | solo superusuario |
| `LAB-04` | Descargar el reporte de la sala | Técnico de Laboratorio | solo superusuario |
| `LAB-04` | Descargar el reporte de la sala | Estudiante | solo superusuario |
| `LAB-04` | Descargar el reporte de la sala | Profesor | solo superusuario |
| `LAB-04` | Descargar el reporte de la sala | Regente | solo superusuario |
| `LAB-04` | Descargar el reporte de la sala | Solo Lectura | solo superusuario |
| `LAB-05` | Dar de alta una entrada de catálogo desde el formulario | Administrativo superior | solo superusuario |
| `LAB-05` | Dar de alta una entrada de catálogo desde el formulario | Administrador de Laboratorio | solo superusuario |
| `LAB-05` | Dar de alta una entrada de catálogo desde el formulario | Creador de laboratorio | solo superusuario |
| `LAB-05` | Dar de alta una entrada de catálogo desde el formulario | Asistente de laboratorio | solo superusuario |
| `LAB-05` | Consultar tipos de equipo y familias instrumentales | Administrativo superior | solo superusuario |
| `LAB-05` | Consultar tipos de equipo y familias instrumentales | Administrador de Laboratorio | solo superusuario |
| `LAB-05` | Consultar tipos de equipo y familias instrumentales | Creador de laboratorio | solo superusuario |
| `LAB-05` | Consultar tipos de equipo y familias instrumentales | Asistente de laboratorio | solo superusuario |
| `LAB-05` | Consultar tipos de equipo y familias instrumentales | Técnico de Laboratorio | solo superusuario |
| `LAB-05` | Consultar tipos de equipo y familias instrumentales | Estudiante | solo superusuario |
| `LAB-05` | Consultar tipos de equipo y familias instrumentales | Profesor | solo superusuario |
| `LAB-05` | Consultar tipos de equipo y familias instrumentales | Regente | solo superusuario |
| `LAB-05` | Consultar tipos de equipo y familias instrumentales | Solo Lectura | solo superusuario |
| `LAB-06` | Generar y administrar los QR de registro | Administrativo superior | solo superusuario |
| `LAB-06` | Generar y administrar los QR de registro | Administrador de Laboratorio | solo superusuario |
| `LAB-06` | Generar y administrar los QR de registro | Creador de laboratorio | solo superusuario |
| `LAB-06` | Generar y administrar los QR de registro | Asistente de laboratorio | solo superusuario |
| `LAB-06` | Descargar el PDF con el QR | Administrativo superior | solo superusuario |
| `LAB-06` | Descargar el PDF con el QR | Administrador de Laboratorio | solo superusuario |
| `LAB-06` | Descargar el PDF con el QR | Creador de laboratorio | solo superusuario |
| `LAB-06` | Descargar el PDF con el QR | Asistente de laboratorio | solo superusuario |
| `LAB-06` | Escanear el QR y quedar registrado en el laboratorio | Estudiante | nunca ejercitado |
| `LAB-06` | Escanear el QR y quedar registrado en el laboratorio | Profesor | nunca ejercitado |
| `LAB-06` | Escanear el QR y quedar registrado en el laboratorio | Anónimo | nunca ejercitado |
| `LAB-06` | Consultar quién entró por el QR | Administrativo superior | solo superusuario |
| `LAB-06` | Consultar quién entró por el QR | Administrador de Laboratorio | solo superusuario |
| `LAB-06` | Consultar quién entró por el QR | Creador de laboratorio | solo superusuario |
| `LAB-06` | Consultar quién entró por el QR | Asistente de laboratorio | solo superusuario |
| `LAB-06` | Retirar un QR de registro | Administrativo superior | solo superusuario |
| `LAB-06` | Retirar un QR de registro | Administrador de Laboratorio | solo superusuario |
| `LAB-06` | Retirar un QR de registro | Creador de laboratorio | solo superusuario |
| `LAB-06` | Retirar un QR de registro | Asistente de laboratorio | solo superusuario |
| `LAB-07` | Consultar la bitácora de la organización | Administrativo superior | solo superusuario |
| `LAB-07` | Consultar la bitácora de la organización | Administrador de Laboratorio | solo superusuario |
| `LAB-07` | Consultar la bitácora de la organización | Regente | solo superusuario |
| `LAB-07` | Consultar la bitácora de la organización | Solo Lectura | solo superusuario |
| `LAB-07` | Ver la papelera y recuperar un elemento | Administrativo superior | solo superusuario |
| `LAB-07` | Ver la papelera y recuperar un elemento | Administrador de Laboratorio | solo superusuario |
| `LAB-08` | Ver y editar el perfil | Administrativo superior | solo superusuario |
| `LAB-08` | Ver y editar el perfil | Administrador de Laboratorio | solo superusuario |
| `LAB-08` | Ver y editar el perfil | Creador de laboratorio | solo superusuario |
| `LAB-08` | Ver y editar el perfil | Asistente de laboratorio | solo superusuario |
| `LAB-08` | Ver y editar el perfil | Técnico de Laboratorio | solo superusuario |
| `LAB-08` | Ver y editar el perfil | Estudiante | solo superusuario |
| `LAB-08` | Ver y editar el perfil | Profesor | solo superusuario |
| `LAB-08` | Ver y editar el perfil | Regente | solo superusuario |
| `LAB-08` | Ver y editar el perfil | Solo Lectura | solo superusuario |
| `LAB-08` | Cambiar la contraseña | Administrativo superior | solo superusuario |
| `LAB-08` | Cambiar la contraseña | Administrador de Laboratorio | solo superusuario |
| `LAB-08` | Cambiar la contraseña | Creador de laboratorio | solo superusuario |
| `LAB-08` | Cambiar la contraseña | Asistente de laboratorio | solo superusuario |
| `LAB-08` | Cambiar la contraseña | Técnico de Laboratorio | solo superusuario |
| `LAB-08` | Cambiar la contraseña | Estudiante | solo superusuario |
| `LAB-08` | Cambiar la contraseña | Profesor | solo superusuario |
| `LAB-08` | Cambiar la contraseña | Regente | solo superusuario |
| `LAB-08` | Cambiar la contraseña | Solo Lectura | solo superusuario |
| `TASK-01` | Ver mis tareas pendientes | Estudiante | solo superusuario |
| `TASK-01` | Ver mis tareas pendientes | Profesor | solo superusuario |
| `TASK-01` | Ver mis tareas pendientes | Técnico de Laboratorio | solo superusuario |
| `TASK-01` | Ver mis tareas pendientes | Asistente de laboratorio | solo superusuario |
| `TASK-01` | Ver mis tareas pendientes | Administrador de Laboratorio | solo superusuario |
| `TASK-01` | Ver mis tareas pendientes | Administrativo superior | solo superusuario |
| `TASK-01` | Ver mis tareas pendientes | Regente | solo superusuario |
| `TASK-01` | Ver mis tareas pendientes | Solo Lectura | solo superusuario |
| `MSDS-01` | Consultar el árbol de fichas | Estudiante | solo superusuario |
| `MSDS-01` | Consultar el árbol de fichas | Profesor | solo superusuario |
| `MSDS-01` | Consultar el árbol de fichas | Técnico de Laboratorio | solo superusuario |
| `MSDS-01` | Consultar el árbol de fichas | Asistente de laboratorio | solo superusuario |
| `MSDS-01` | Consultar el árbol de fichas | Administrador de Laboratorio | solo superusuario |
| `MSDS-01` | Consultar el árbol de fichas | Administrativo superior | solo superusuario |
| `MSDS-01` | Consultar el árbol de fichas | Regente | solo superusuario |
| `MSDS-01` | Consultar el árbol de fichas | Solo Lectura | solo superusuario |
| `MSDS-01` | Registrar una ficha | Administrador de Laboratorio | solo superusuario |
| `MSDS-01` | Registrar una ficha | Técnico de Laboratorio | solo superusuario |
| `MSDS-01` | Registrar una ficha | SGA | solo superusuario |
| `MSDS-01` | Verificar la trazabilidad de las fichas extraídas | SGA | solo superusuario |
| `MSDS-01` | Verificar la trazabilidad de las fichas extraídas | Regente | solo superusuario |
| `MSDS-01` | Verificar la trazabilidad de las fichas extraídas | Administrativo superior | solo superusuario |
| `DERB-01` | Listar los formularios de la organización | Administrador de Laboratorio | solo superusuario |
| `DERB-01` | Listar los formularios de la organización | Administrativo superior | solo superusuario |
| `DERB-01` | Listar los formularios de la organización | Profesor | solo superusuario |
| `DERB-01` | Crear un formulario | Administrador de Laboratorio | solo superusuario |
| `DERB-01` | Crear un formulario | Administrativo superior | solo superusuario |
| `DERB-01` | Editar el formulario en el constructor | Administrador de Laboratorio | solo superusuario |
| `DERB-01` | Editar el formulario en el constructor | Administrativo superior | solo superusuario |
| `DERB-01` | Previsualizar el formulario tal como lo verá quien lo rellene | Administrador de Laboratorio | solo superusuario |
| `DERB-01` | Previsualizar el formulario tal como lo verá quien lo rellene | Administrativo superior | solo superusuario |
| `DERB-01` | Previsualizar el formulario tal como lo verá quien lo rellene | Profesor | solo superusuario |
| `DERB-01` | Borrar un formulario | Administrador de Laboratorio | solo superusuario |
| `DERB-01` | Borrar un formulario | Administrativo superior | solo superusuario |
| `GEN-01` | Abrir la portada y la información general | Anónimo | solo superusuario |
| `GEN-01` | Abrir la portada y la información general | Estudiante | solo superusuario |
| `GEN-01` | Abrir la portada y la información general | Profesor | solo superusuario |
| `GEN-01` | Abrir la portada y la información general | Técnico de Laboratorio | solo superusuario |
| `GEN-01` | Abrir la portada y la información general | Asistente de laboratorio | solo superusuario |
| `GEN-01` | Abrir la portada y la información general | Administrador de Laboratorio | solo superusuario |
| `GEN-01` | Abrir la portada y la información general | Administrativo superior | solo superusuario |
| `GEN-01` | Abrir la portada y la información general | Regente | solo superusuario |
| `GEN-01` | Abrir la portada y la información general | Solo Lectura | solo superusuario |
| `GEN-01` | Consultar y descargar los documentos de regulación | Anónimo | solo superusuario |
| `GEN-01` | Consultar y descargar los documentos de regulación | Estudiante | solo superusuario |
| `GEN-01` | Consultar y descargar los documentos de regulación | Profesor | solo superusuario |
| `GEN-01` | Consultar y descargar los documentos de regulación | Técnico de Laboratorio | solo superusuario |
| `GEN-01` | Consultar y descargar los documentos de regulación | Asistente de laboratorio | solo superusuario |
| `GEN-01` | Consultar y descargar los documentos de regulación | Administrador de Laboratorio | solo superusuario |
| `GEN-01` | Consultar y descargar los documentos de regulación | Administrativo superior | solo superusuario |
| `GEN-01` | Consultar y descargar los documentos de regulación | Regente | solo superusuario |
| `GEN-01` | Consultar y descargar los documentos de regulación | Solo Lectura | solo superusuario |
| `GEN-01` | Ver la pantalla de acceso denegado | Anónimo | solo superusuario |
| `GEN-01` | Ver la pantalla de acceso denegado | Estudiante | solo superusuario |
| `GEN-01` | Ver la pantalla de acceso denegado | Profesor | solo superusuario |
| `GEN-01` | Ver la pantalla de acceso denegado | Técnico de Laboratorio | solo superusuario |
| `GEN-01` | Ver la pantalla de acceso denegado | Asistente de laboratorio | solo superusuario |
| `GEN-01` | Ver la pantalla de acceso denegado | Administrador de Laboratorio | solo superusuario |
| `GEN-01` | Ver la pantalla de acceso denegado | Administrativo superior | solo superusuario |
| `GEN-01` | Ver la pantalla de acceso denegado | Regente | solo superusuario |
| `GEN-01` | Ver la pantalla de acceso denegado | Solo Lectura | solo superusuario |
| `GEN-02` | Ver los tutoriales disponibles | Estudiante | solo superusuario |
| `GEN-02` | Ver los tutoriales disponibles | Profesor | solo superusuario |
| `GEN-02` | Ver los tutoriales disponibles | Técnico de Laboratorio | solo superusuario |
| `GEN-02` | Ver los tutoriales disponibles | Asistente de laboratorio | solo superusuario |
| `GEN-02` | Ver los tutoriales disponibles | Administrador de Laboratorio | solo superusuario |
| `GEN-02` | Ver los tutoriales disponibles | Administrativo superior | solo superusuario |
| `GEN-02` | Ver los tutoriales disponibles | Regente | solo superusuario |
| `GEN-02` | Ver los tutoriales disponibles | Solo Lectura | solo superusuario |
| `GEN-02` | Marcar progreso, apagar y reactivar un tutorial | Estudiante | solo superusuario |
| `GEN-02` | Marcar progreso, apagar y reactivar un tutorial | Profesor | solo superusuario |
| `GEN-02` | Marcar progreso, apagar y reactivar un tutorial | Técnico de Laboratorio | solo superusuario |
| `GEN-02` | Marcar progreso, apagar y reactivar un tutorial | Asistente de laboratorio | solo superusuario |
| `GEN-02` | Marcar progreso, apagar y reactivar un tutorial | Administrador de Laboratorio | solo superusuario |
| `GEN-02` | Marcar progreso, apagar y reactivar un tutorial | Administrativo superior | solo superusuario |
| `GEN-02` | Marcar progreso, apagar y reactivar un tutorial | Regente | solo superusuario |
| `GEN-02` | Marcar progreso, apagar y reactivar un tutorial | Solo Lectura | solo superusuario |
| `GEN-02` | Enviar retroalimentación sobre el producto | Estudiante | solo superusuario |
| `GEN-02` | Enviar retroalimentación sobre el producto | Profesor | solo superusuario |
| `GEN-02` | Enviar retroalimentación sobre el producto | Técnico de Laboratorio | solo superusuario |
| `GEN-02` | Enviar retroalimentación sobre el producto | Asistente de laboratorio | solo superusuario |
| `GEN-02` | Enviar retroalimentación sobre el producto | Administrador de Laboratorio | solo superusuario |
| `GEN-02` | Enviar retroalimentación sobre el producto | Administrativo superior | solo superusuario |
| `GEN-02` | Enviar retroalimentación sobre el producto | Regente | solo superusuario |
| `GEN-02` | Enviar retroalimentación sobre el producto | Solo Lectura | solo superusuario |
| `REP-01` | Elegir el reporte y sus parámetros | Administrativo superior | solo superusuario |
| `REP-01` | Elegir el reporte y sus parámetros | Administrador de Laboratorio | solo superusuario |
| `REP-01` | Elegir el reporte y sus parámetros | Regente | solo superusuario |
| `REP-01` | Elegir el reporte y sus parámetros | Asistente de laboratorio | solo superusuario |
| `REP-01` | Elegir el reporte y sus parámetros | Solo Lectura | solo superusuario |
| `REP-01` | Elegir el reporte y sus parámetros | Administrativo de centro de trabajo | solo superusuario |
| `REP-01` | Encolar la generación del reporte | Administrativo superior | solo superusuario |
| `REP-01` | Encolar la generación del reporte | Administrador de Laboratorio | solo superusuario |
| `REP-01` | Encolar la generación del reporte | Regente | solo superusuario |
| `REP-01` | Encolar la generación del reporte | Asistente de laboratorio | solo superusuario |
| `REP-01` | Encolar la generación del reporte | Solo Lectura | solo superusuario |
| `REP-01` | Encolar la generación del reporte | Administrativo de centro de trabajo | solo superusuario |
| `REP-01` | Consultar el estado hasta que la tarea termina | Administrativo superior | solo superusuario |
| `REP-01` | Consultar el estado hasta que la tarea termina | Administrador de Laboratorio | solo superusuario |
| `REP-01` | Consultar el estado hasta que la tarea termina | Regente | solo superusuario |
| `REP-01` | Consultar el estado hasta que la tarea termina | Asistente de laboratorio | solo superusuario |
| `REP-01` | Consultar el estado hasta que la tarea termina | Solo Lectura | solo superusuario |
| `REP-01` | Consultar el estado hasta que la tarea termina | Administrativo de centro de trabajo | solo superusuario |
| `REP-01` | Abrir el resultado en pantalla | Administrativo superior | solo superusuario |
| `REP-01` | Abrir el resultado en pantalla | Administrador de Laboratorio | solo superusuario |
| `REP-01` | Abrir el resultado en pantalla | Regente | solo superusuario |
| `REP-01` | Abrir el resultado en pantalla | Asistente de laboratorio | solo superusuario |
| `REP-01` | Abrir el resultado en pantalla | Solo Lectura | solo superusuario |
| `REP-01` | Abrir el resultado en pantalla | Administrativo de centro de trabajo | solo superusuario |
| `REP-01` | Descargar el fichero generado | Administrativo superior | solo superusuario |
| `REP-01` | Descargar el fichero generado | Administrador de Laboratorio | solo superusuario |
| `REP-01` | Descargar el fichero generado | Regente | solo superusuario |
| `REP-01` | Descargar el fichero generado | Asistente de laboratorio | solo superusuario |
| `REP-01` | Descargar el fichero generado | Solo Lectura | solo superusuario |
| `REP-01` | Descargar el fichero generado | Administrativo de centro de trabajo | solo superusuario |
| `REP-02` | Consultar el reporte de precursores y sus valores | Administrativo superior | solo superusuario |
| `REP-02` | Consultar el reporte de precursores y sus valores | Administrador de Laboratorio | solo superusuario |
| `REP-02` | Consultar el reporte de precursores y sus valores | Regente | solo superusuario |
| `REP-02` | Consultar el reporte de precursores y sus valores | Asistente de laboratorio | solo superusuario |
| `REP-02` | Consultar el reporte de precursores y sus valores | Solo Lectura | solo superusuario |
| `REP-02` | Consultar el reporte de precursores y sus valores | Administrativo de centro de trabajo | solo superusuario |
| `REP-03` | Generar el reporte de regencia | Regente | solo superusuario |
| `REP-03` | Generar el reporte de regencia | Administrativo superior | solo superusuario |
| `REP-04` | Abrir el mapa de peligros | Administrativo superior | solo superusuario |
| `REP-04` | Abrir el mapa de peligros | Administrador de Laboratorio | solo superusuario |
| `REP-04` | Abrir el mapa de peligros | Regente | solo superusuario |
| `REP-04` | Abrir el mapa de peligros | Asistente de laboratorio | solo superusuario |
| `REP-04` | Abrir el mapa de peligros | Solo Lectura | solo superusuario |
| `REP-04` | Abrir el mapa de peligros | Administrativo de centro de trabajo | solo superusuario |
| `RES-01` | Reservar desde el estante (reserva directa) | Estudiante | nunca ejercitado |
| `RES-01` | Reservar desde el estante (reserva directa) | Profesor | nunca ejercitado |
| `RES-01` | Reservar desde el estante (reserva directa) | Técnico de Laboratorio | nunca ejercitado |
| `RES-01` | Reservar desde el estante (reserva directa) | Asistente de laboratorio | nunca ejercitado |
| `RES-01` | Reservar desde el estante (reserva directa) | Estudiante | nunca ejercitado |
| `RES-01` | Solicitar la reserva desde un procedimiento | Profesor | solo superusuario |
| `RES-01` | Solicitar la reserva desde un procedimiento | Estudiante | solo superusuario |
| `RES-01` | Consultar mis reservas | Estudiante | ejercitado |
| `RES-01` | Consultar mis reservas | Técnico de Laboratorio | ejercitado |
| `RES-01` | Consultar mis reservas | Asistente de laboratorio | ejercitado |
| `RES-01` | Ver la cola de reservas por estado | Administrativo de centro de trabajo | ejercitado |
| `RES-01` | Ver la cola de reservas por estado | Asistente de laboratorio | ejercitado |
| `RES-01` | Ver la cola de reservas por estado | Regente | ejercitado |
| `RES-01` | Ver la cola de reservas por estado | Solo Lectura | ejercitado |
| `RES-01` | Aceptar o rechazar la reserva completa | Administrativo de centro de trabajo | ejercitado |
| `RES-01` | Aceptar o rechazar la reserva completa | Asistente de laboratorio | ejercitado |
| `RES-01` | Aceptar o rechazar un producto suelto de la reserva | Administrador de Laboratorio | nunca ejercitado |
| `RES-01` | Aceptar o rechazar un producto suelto de la reserva | Administrativo de centro de trabajo | nunca ejercitado |
| `RES-01` | Aceptar o rechazar un producto suelto de la reserva | Asistente de laboratorio | nunca ejercitado |
| `RES-01` | Registrar la devolución y reponer el stock | Técnico de Laboratorio | ejercitado |
| `RES-01` | Comprobar cantidad y disponibilidad antes de confirmar | Estudiante | ejercitado |
| `RES-01` | Comprobar cantidad y disponibilidad antes de confirmar | Profesor | ejercitado |
| `RES-01` | Comprobar cantidad y disponibilidad antes de confirmar | Técnico de Laboratorio | ejercitado |
| `RES-01` | Comprobar cantidad y disponibilidad antes de confirmar | Asistente de laboratorio | ejercitado |
| `RES-01` | Comprobar cantidad y disponibilidad antes de confirmar | Administrativo de centro de trabajo | ejercitado |
| `RES-01` | Comprobar cantidad y disponibilidad antes de confirmar | Asistente de laboratorio | ejercitado |
| `RISK-01` | Listar y abrir el detalle de una zona de riesgo | Administrativo superior | solo superusuario |
| `RISK-01` | Listar y abrir el detalle de una zona de riesgo | Administrador de Laboratorio | solo superusuario |
| `RISK-01` | Listar y abrir el detalle de una zona de riesgo | Regente | solo superusuario |
| `RISK-01` | Listar y abrir el detalle de una zona de riesgo | Asistente de laboratorio | solo superusuario |
| `RISK-01` | Listar y abrir el detalle de una zona de riesgo | Solo Lectura | solo superusuario |
| `RISK-01` | Listar y abrir el detalle de una zona de riesgo | Técnico de Laboratorio | solo superusuario |
| `RISK-01` | Crear una zona de riesgo y su tipo | Administrativo superior | solo superusuario |
| `RISK-01` | Crear una zona de riesgo y su tipo | Administrador de Laboratorio | solo superusuario |
| `RISK-01` | Crear una zona de riesgo y su tipo | Regente | solo superusuario |
| `RISK-01` | Crear una zona de riesgo y su tipo | Asistente de laboratorio | solo superusuario |
| `RISK-01` | Editar o borrar una zona | Administrativo superior | solo superusuario |
| `RISK-01` | Editar o borrar una zona | Administrador de Laboratorio | solo superusuario |
| `RISK-01` | Editar o borrar una zona | Regente | solo superusuario |
| `RISK-01` | Editar o borrar una zona | Asistente de laboratorio | solo superusuario |
| `RISK-01` | Ver el panel de zonas y su reporte | Administrativo superior | solo superusuario |
| `RISK-01` | Ver el panel de zonas y su reporte | Administrador de Laboratorio | solo superusuario |
| `RISK-01` | Ver el panel de zonas y su reporte | Regente | solo superusuario |
| `RISK-01` | Ver el panel de zonas y su reporte | Asistente de laboratorio | solo superusuario |
| `RISK-01` | Ver el panel de zonas y su reporte | Solo Lectura | solo superusuario |
| `RISK-01` | Ver el panel de zonas y su reporte | Técnico de Laboratorio | solo superusuario |
| `RISK-01` | Consultar las jornadas de trabajo de la zona | Administrativo superior | solo superusuario |
| `RISK-01` | Consultar las jornadas de trabajo de la zona | Administrador de Laboratorio | solo superusuario |
| `RISK-01` | Consultar las jornadas de trabajo de la zona | Regente | solo superusuario |
| `RISK-01` | Consultar las jornadas de trabajo de la zona | Asistente de laboratorio | solo superusuario |
| `RISK-01` | Consultar las jornadas de trabajo de la zona | Solo Lectura | solo superusuario |
| `RISK-01` | Consultar las jornadas de trabajo de la zona | Técnico de Laboratorio | solo superusuario |
| `RISK-02` | Registrar un incidente | Administrativo superior | solo superusuario |
| `RISK-02` | Registrar un incidente | Administrador de Laboratorio | solo superusuario |
| `RISK-02` | Registrar un incidente | Regente | solo superusuario |
| `RISK-02` | Registrar un incidente | Asistente de laboratorio | solo superusuario |
| `RISK-02` | Registrar un incidente | Solo Lectura | solo superusuario |
| `RISK-02` | Registrar un incidente | Técnico de Laboratorio | solo superusuario |
| `RISK-02` | Registrar un incidente | Estudiante | solo superusuario |
| `RISK-02` | Registrar un incidente | Profesor | solo superusuario |
| `RISK-02` | Listar incidentes y abrir su detalle | Administrativo superior | solo superusuario |
| `RISK-02` | Listar incidentes y abrir su detalle | Administrador de Laboratorio | solo superusuario |
| `RISK-02` | Listar incidentes y abrir su detalle | Regente | solo superusuario |
| `RISK-02` | Listar incidentes y abrir su detalle | Asistente de laboratorio | solo superusuario |
| `RISK-02` | Listar incidentes y abrir su detalle | Solo Lectura | solo superusuario |
| `RISK-02` | Listar incidentes y abrir su detalle | Técnico de Laboratorio | solo superusuario |
| `RISK-02` | Corregir o eliminar un incidente | Administrativo superior | solo superusuario |
| `RISK-02` | Corregir o eliminar un incidente | Administrador de Laboratorio | solo superusuario |
| `RISK-02` | Corregir o eliminar un incidente | Regente | solo superusuario |
| `RISK-02` | Corregir o eliminar un incidente | Asistente de laboratorio | solo superusuario |
| `RISK-02` | Descargar el reporte de incidentes | Administrativo superior | solo superusuario |
| `RISK-02` | Descargar el reporte de incidentes | Administrador de Laboratorio | solo superusuario |
| `RISK-02` | Descargar el reporte de incidentes | Regente | solo superusuario |
| `RISK-02` | Descargar el reporte de incidentes | Asistente de laboratorio | solo superusuario |
| `RISK-02` | Descargar el reporte de incidentes | Solo Lectura | solo superusuario |
| `RISK-02` | Descargar el reporte de incidentes | Técnico de Laboratorio | solo superusuario |
| `RISK-03` | Listar, crear y editar edificios | Administrativo superior | solo superusuario |
| `RISK-03` | Listar, crear y editar edificios | Administrador de Laboratorio | solo superusuario |
| `RISK-03` | Listar, crear y editar edificios | Regente | solo superusuario |
| `RISK-03` | Listar, crear y editar edificios | Asistente de laboratorio | solo superusuario |
| `RISK-03` | Listar, crear y editar estructuras | Administrativo superior | solo superusuario |
| `RISK-03` | Listar, crear y editar estructuras | Administrador de Laboratorio | solo superusuario |
| `RISK-03` | Listar, crear y editar estructuras | Regente | solo superusuario |
| `RISK-03` | Listar, crear y editar estructuras | Asistente de laboratorio | solo superusuario |
| `RISK-03` | Consultar los regentes del laboratorio | Administrativo superior | solo superusuario |
| `RISK-03` | Consultar los regentes del laboratorio | Administrador de Laboratorio | solo superusuario |
| `RISK-03` | Consultar los regentes del laboratorio | Regente | solo superusuario |
| `RISK-03` | Consultar los regentes del laboratorio | Asistente de laboratorio | solo superusuario |
| `RISK-03` | Consultar los regentes del laboratorio | Solo Lectura | solo superusuario |
| `RISK-03` | Consultar los regentes del laboratorio | Técnico de Laboratorio | solo superusuario |
| `IPER-01` | Solicitar a los laboratorios de una zona que llenen su IPER | Administrador IPER | nunca ejercitado |
| `IPER-01` | Solicitar a los laboratorios de una zona que llenen su IPER | Administrativo superior | nunca ejercitado |
| `IPER-01` | Crear la evaluación del laboratorio | Administrador de Laboratorio | solo superusuario |
| `IPER-01` | Crear la evaluación del laboratorio | Regente asignado al laboratorio | solo superusuario |
| `IPER-01` | Crear la evaluación del laboratorio | Administrador IPER | solo superusuario |
| `IPER-01` | Identificar peligros y valorar el riesgo | Administrador de Laboratorio | solo superusuario |
| `IPER-01` | Identificar peligros y valorar el riesgo | Regente asignado al laboratorio | solo superusuario |
| `IPER-01` | Identificar peligros y valorar el riesgo | Administrador IPER | solo superusuario |
| `IPER-01` | Marcar la evaluación como completada (o devolverla a borrador) | Administrador de Laboratorio | nunca ejercitado |
| `IPER-01` | Marcar la evaluación como completada (o devolverla a borrador) | Regente asignado al laboratorio | nunca ejercitado |
| `IPER-01` | Marcar la evaluación como completada (o devolverla a borrador) | Administrador IPER | nunca ejercitado |
| `IPER-01` | Clonar la evaluación para actualizarla | Administrador de Laboratorio | solo superusuario |
| `IPER-01` | Clonar la evaluación para actualizarla | Regente asignado al laboratorio | solo superusuario |
| `IPER-01` | Clonar la evaluación para actualizarla | Administrador IPER | solo superusuario |
| `IPER-01` | Observar la evaluación sin poder modificarla | Auditor IPER | nunca ejercitado |
| `IPER-01` | Listar evaluaciones, ver el detalle y su histórico | Auditor IPER | solo superusuario |
| `IPER-01` | Listar evaluaciones, ver el detalle y su histórico | Administrador IPER | solo superusuario |
| `IPER-01` | Listar evaluaciones, ver el detalle y su histórico | Administrador de Laboratorio | solo superusuario |
| `IPER-01` | Listar evaluaciones, ver el detalle y su histórico | Regente | solo superusuario |
| `IPER-01` | Listar evaluaciones, ver el detalle y su histórico | Solo Lectura | solo superusuario |
| `IPER-01` | Ver el panel consolidado de IPER | Administrador IPER | solo superusuario |
| `IPER-01` | Ver el panel consolidado de IPER | Administrativo superior | solo superusuario |
| `IPER-01` | Ver el panel consolidado de IPER | Auditor IPER | solo superusuario |
| `IPER-01` | Alternar el anonimato de la evaluación | Administrador de Laboratorio | nunca ejercitado |
| `IPER-01` | Alternar el anonimato de la evaluación | Administrador IPER | nunca ejercitado |
| `IPER-01` | Mantener el catálogo IPER de la organización raíz | Administrador IPER | nunca ejercitado |
| `IPER-01` | Eliminar una evaluación | Administrador IPER | nunca ejercitado |
| `IPER-01` | Eliminar una evaluación | Administrativo superior | nunca ejercitado |
| `SGA-01` | Abrir el asistente y describir la sustancia (paso 1) | SGA | solo superusuario |
| `SGA-01` | Abrir el asistente y describir la sustancia (paso 1) | Administrador de Laboratorio | solo superusuario |
| `SGA-01` | Abrir el asistente y describir la sustancia (paso 1) | Técnico de Laboratorio | solo superusuario |
| `SGA-01` | Abrir el asistente y describir la sustancia (paso 1) | Lectura y agregado de sustancias | solo superusuario |
| `SGA-01` | Abrir el asistente y describir la sustancia (paso 1) | Manejo de sustancias del laboratorio | solo superusuario |
| `SGA-01` | Completar la hoja de seguridad (paso 4) | SGA | solo superusuario |
| `SGA-01` | Completar la hoja de seguridad (paso 4) | Administrador de Laboratorio | solo superusuario |
| `SGA-01` | Completar la hoja de seguridad (paso 4) | Técnico de Laboratorio | solo superusuario |
| `SGA-01` | Completar la hoja de seguridad (paso 4) | Lectura y agregado de sustancias | solo superusuario |
| `SGA-01` | Completar la hoja de seguridad (paso 4) | Manejo de sustancias del laboratorio | solo superusuario |
| `SGA-01` | Subir la ficha de datos de seguridad y seguir la extracción | SGA | solo superusuario |
| `SGA-01` | Subir la ficha de datos de seguridad y seguir la extracción | Administrador de Laboratorio | solo superusuario |
| `SGA-01` | Subir la ficha de datos de seguridad y seguir la extracción | Técnico de Laboratorio | solo superusuario |
| `SGA-01` | Subir la ficha de datos de seguridad y seguir la extracción | Lectura y agregado de sustancias | solo superusuario |
| `SGA-01` | Subir la ficha de datos de seguridad y seguir la extracción | Manejo de sustancias del laboratorio | solo superusuario |
| `SGA-01` | Añadir el proveedor de la sustancia | SGA | solo superusuario |
| `SGA-01` | Añadir el proveedor de la sustancia | Administrador de Laboratorio | solo superusuario |
| `SGA-01` | Añadir el proveedor de la sustancia | Técnico de Laboratorio | solo superusuario |
| `SGA-01` | Añadir el proveedor de la sustancia | Lectura y agregado de sustancias | solo superusuario |
| `SGA-01` | Añadir el proveedor de la sustancia | Manejo de sustancias del laboratorio | solo superusuario |
| `SGA-01` | Enviar la sustancia a revisión | SGA | solo superusuario |
| `SGA-01` | Enviar la sustancia a revisión | Administrador de Laboratorio | solo superusuario |
| `SGA-01` | Enviar la sustancia a revisión | Técnico de Laboratorio | solo superusuario |
| `SGA-01` | Enviar la sustancia a revisión | Lectura y agregado de sustancias | solo superusuario |
| `SGA-01` | Enviar la sustancia a revisión | Manejo de sustancias del laboratorio | solo superusuario |
| `SGA-01` | Ver la bandeja de sustancias por aprobar | Administrativo superior | solo superusuario |
| `SGA-01` | Ver la bandeja de sustancias por aprobar | SGA | solo superusuario |
| `SGA-01` | Ver la bandeja de sustancias por aprobar | Organization Management | solo superusuario |
| `SGA-01` | Dejar, editar o borrar observaciones sobre la sustancia | Administrativo superior | solo superusuario |
| `SGA-01` | Dejar, editar o borrar observaciones sobre la sustancia | SGA | solo superusuario |
| `SGA-01` | Dejar, editar o borrar observaciones sobre la sustancia | Organization Management | solo superusuario |
| `SGA-01` | Dejar, editar o borrar observaciones sobre la sustancia | Administrador de Laboratorio | solo superusuario |
| `SGA-01` | Abrir el detalle de la sustancia en revisión | Administrativo superior | solo superusuario |
| `SGA-01` | Abrir el detalle de la sustancia en revisión | SGA | solo superusuario |
| `SGA-01` | Abrir el detalle de la sustancia en revisión | Organization Management | solo superusuario |
| `SGA-01` | Aprobar la sustancia | Administrativo superior | solo superusuario |
| `SGA-01` | Aprobar la sustancia | SGA | solo superusuario |
| `SGA-01` | Aprobar la sustancia | Organization Management | solo superusuario |
| `SGA-01` | Eliminar la sustancia | Administrativo superior | solo superusuario |
| `SGA-01` | Eliminar la sustancia | SGA | solo superusuario |
| `SGA-01` | Eliminar la sustancia | Organization Management | solo superusuario |
| `SGA-01` | Eliminar la sustancia | Administrador de Laboratorio | solo superusuario |
| `SGA-02` | Generar la etiqueta de la sustancia | SGA | solo superusuario |
| `SGA-02` | Generar la etiqueta de la sustancia | Administrador de Laboratorio | solo superusuario |
| `SGA-02` | Generar la etiqueta de la sustancia | Técnico de Laboratorio | solo superusuario |
| `SGA-02` | Generar la etiqueta de la sustancia | Regente | solo superusuario |
| `SGA-02` | Generar la etiqueta de la sustancia | Solo Lectura | solo superusuario |
| `SGA-02` | Generar la etiqueta de la sustancia | Estudiante | solo superusuario |
| `SGA-02` | Descargar la hoja de seguridad en PDF | SGA | nunca ejercitado |
| `SGA-02` | Descargar la hoja de seguridad en PDF | Administrador de Laboratorio | nunca ejercitado |
| `SGA-02` | Descargar la hoja de seguridad en PDF | Técnico de Laboratorio | nunca ejercitado |
| `SGA-02` | Descargar la hoja de seguridad en PDF | Regente | nunca ejercitado |
| `SGA-02` | Descargar la hoja de seguridad en PDF | Solo Lectura | nunca ejercitado |
| `SGA-02` | Descargar la hoja de seguridad en PDF | Estudiante | nunca ejercitado |
| `SGA-02` | Consultar los complementos SGA de una sustancia | SGA | nunca ejercitado |
| `SGA-02` | Consultar los complementos SGA de una sustancia | Administrador de Laboratorio | nunca ejercitado |
| `SGA-02` | Consultar los complementos SGA de una sustancia | Técnico de Laboratorio | nunca ejercitado |
| `SGA-02` | Consultar los complementos SGA de una sustancia | Regente | nunca ejercitado |
| `SGA-02` | Consultar los complementos SGA de una sustancia | Solo Lectura | nunca ejercitado |
| `SGA-02` | Consultar los complementos SGA de una sustancia | Estudiante | nunca ejercitado |
| `SGA-03` | Consultar frases H, frases P y palabras de advertencia | SGA | solo superusuario |
| `SGA-03` | Consultar frases H, frases P y palabras de advertencia | Administrador de Laboratorio | solo superusuario |
| `SGA-03` | Consultar frases H, frases P y palabras de advertencia | Técnico de Laboratorio | solo superusuario |
| `SGA-03` | Consultar frases H, frases P y palabras de advertencia | Regente | solo superusuario |
| `SGA-03` | Consultar frases H, frases P y palabras de advertencia | Solo Lectura | solo superusuario |
| `SGA-03` | Consultar frases H, frases P y palabras de advertencia | Estudiante | solo superusuario |
| `SGA-03` | Dar de alta una frase o palabra de advertencia | SGA | solo superusuario |
| `SGA-03` | Dar de alta una frase o palabra de advertencia | Administrativo superior | solo superusuario |
| `SGA-03` | Editar una frase o palabra de advertencia | SGA | solo superusuario |
| `SGA-03` | Editar una frase o palabra de advertencia | Administrativo superior | solo superusuario |
| `SGA-03` | Consultar sustancias peligrosas y sus categorías | SGA | solo superusuario |
| `SGA-03` | Consultar sustancias peligrosas y sus categorías | Administrador de Laboratorio | solo superusuario |
| `SGA-03` | Consultar sustancias peligrosas y sus categorías | Técnico de Laboratorio | solo superusuario |
| `SGA-03` | Consultar sustancias peligrosas y sus categorías | Regente | solo superusuario |
| `SGA-03` | Consultar sustancias peligrosas y sus categorías | Solo Lectura | solo superusuario |
| `SGA-03` | Consultar sustancias peligrosas y sus categorías | Estudiante | solo superusuario |
| `SGA-04` | Abrir el editor de plantillas | SGA | solo superusuario |
| `SGA-04` | Abrir el editor de plantillas | Administrativo superior | solo superusuario |
| `SGA-04` | Abrir el editor de plantillas | Administrador de Laboratorio | solo superusuario |
| `SGA-04` | Crear una plantilla personal | SGA | solo superusuario |
| `SGA-04` | Crear una plantilla personal | Administrativo superior | solo superusuario |
| `SGA-04` | Crear una plantilla personal | Administrador de Laboratorio | solo superusuario |
| `SGA-04` | Editar la plantilla paso a paso | SGA | solo superusuario |
| `SGA-04` | Editar la plantilla paso a paso | Administrativo superior | solo superusuario |
| `SGA-04` | Editar la plantilla paso a paso | Administrador de Laboratorio | solo superusuario |
| `SGA-04` | Previsualizar la etiqueta y su código de barras | SGA | solo superusuario |
| `SGA-04` | Previsualizar la etiqueta y su código de barras | Administrativo superior | solo superusuario |
| `SGA-04` | Previsualizar la etiqueta y su código de barras | Administrador de Laboratorio | solo superusuario |
| `SGA-04` | Borrar una plantilla | SGA | nunca ejercitado |
| `SGA-04` | Borrar una plantilla | Administrativo superior | nunca ejercitado |
| `SGA-05` | Listar y consultar empresas | SGA | solo superusuario |
| `SGA-05` | Listar y consultar empresas | Administrativo superior | solo superusuario |
| `SGA-05` | Listar y consultar empresas | Administrador de Laboratorio | solo superusuario |
| `SGA-05` | Crear o editar una empresa | SGA | solo superusuario |
| `SGA-05` | Crear o editar una empresa | Administrativo superior | solo superusuario |
| `SGA-05` | Quitar una empresa | SGA | solo superusuario |
| `SGA-05` | Quitar una empresa | Administrativo superior | solo superusuario |
| `SGA-05` | Consultar y dar de alta tamaños de recipiente | SGA | solo superusuario |
| `SGA-05` | Consultar y dar de alta tamaños de recipiente | Administrativo superior | solo superusuario |
| `SGA-05` | Consultar y dar de alta tamaños de recipiente | Administrador de Laboratorio | solo superusuario |
| `SGA-05` | Consultar y dar de alta tamaños de recipiente | Depositante de residuos | solo superusuario |

