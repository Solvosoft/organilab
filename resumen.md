# Migración de características de sustancias a SGA

Resumen de lo desarrollado en la rama `updated_substance_sga`.

## Objetivo

Centralizar en el módulo **SGA** la gestión de características de sustancias químicas, que
hasta ahora vivía duplicada entre `laboratory` y `sga`, y convertir la trazabilidad de fichas
de seguridad (SDS) en parte natural del alta de sustancias en lugar de un registro que solo
generaban los scripts automáticos.

Tres metas concretas:

1. **Una sola fuente de verdad.** `laboratory.SustanceCharacteristics` desaparece del código
   activo; toda lectura y escritura pasa por `sga.SubstanceCharacteristics`.
2. **Un solo camino de alta.** El asistente de SGA es el único sitio donde se crean
   sustancias; se retiran los flujos paralelos y los pasos duplicados.
3. **Trazabilidad real de las fichas.** Al subir una SDS se registra de dónde vino y cuándo,
   se encola su lectura automática y los datos extraídos se proponen en el formulario.

## Qué cambia para quien usa el sistema

- **El asistente pasa de cuatro pasos a tres**: Sustancia → Hoja de seguridad → Enviar a
  revisión. La edición del complemento SGA y de la etiqueta siguen disponibles desde el editor
  SGA, que ya las ofrecía.
- **Al subir la ficha de seguridad**, el sistema la lee en segundo plano y rellena los campos
  que consigue reconocer (CAS, fórmula, densidad, códigos H, clase de almacenamiento…). Es una
  propuesta: hay que revisarla, y solo rellena lo que esté vacío. Un campo con algo escrito no
  se toca, y un conjunto de códigos ya elegido no se sustituye.
- **Cada subida deja su propia entrada de trazabilidad**, así que puede verse cómo ha
  evolucionado la ficha de una sustancia a lo largo del tiempo.
- **Una solicitud puede pedir la sustancia para varios laboratorios a la vez.** Antes había que
  repetir el alta entera por cada uno. Al aprobarla se sigue creando un único reactivo —el
  inventario es de la organización, no del laboratorio—, pero su alta queda registrada en la
  bitácora de cada laboratorio que la pidió, cosa que antes no ocurría en ninguno: el
  laboratorio se guardaba y la aprobación lo ignoraba.
- **El reactivo aprobado ya nace con código**, y con uno por laboratorio. Antes quedaba vacío y
  alguien tenía que rellenarlo a mano. El código sigue la fórmula del Etiquetador y se arma en
  dos tiempos: al aprobar se emite la parte que identifica la sustancia en ese laboratorio
  —`EQ-QUG-CIE-000034`, con las siglas del laboratorio y de la organización— y al colocar cada
  envase en un estante se le añade su lote —`-2026-08-0001`—, que es lo que se imprime en la
  etiqueta. El consecutivo cuenta los envases de esa sustancia en ese laboratorio y vuelve a 1
  cada mes.
- **Los laboratorios y las organizaciones tienen sigla de tres letras.** La deriva una migración
  a partir del nombre —respetando la que el propio nombre declare entre paréntesis— y se puede
  corregir desde el admin.
- **El módulo SGA vuelve a ser accesible.** El permiso que abre todas sus pantallas,
  `institution_can_access`, solo lo concedía un rol asignado a una única persona, así que en la
  práctica nadie podía crear ni revisar sustancias. Ahora lo tienen los roles que ya gestionaban
  sustancias.
- **La opción «Crear sustancias» vuelve a aparecer en el menú.** Estaba protegida por un
  permiso mal escrito (`sga.add_sustancecharacteristics`, sin la «b»), que no existe, de modo
  que nunca se mostraba a nadie.

## El proceso de migración de datos

Esta es la parte delicada de la entrega: mueve datos reales y una de sus operaciones elimina
una columna. Se diseñó para que sea **verificable, rápida y reversible**.

### Punto de partida medido

Sobre un volcado de producción restaurado:

| Dato | Volumen |
|---|---|
| `laboratory.SustanceCharacteristics` a migrar | 2 692 |
| Relaciones M2M a copiar | 21 009 |
| `SDSTraceability` a repuntar | 2 379 |
| `sga.SubstanceCharacteristics` preexistentes | 8 |

Producción estaba en `laboratory 0199` y `sga 0083`, mientras que la rama arranca desde
`laboratory 0208` / `sga 0084`. **El despliegue aplica 34 migraciones**, no solo las quince de
esta rama: las intermedias vienen de `development` y son ligeras.

### Secuencia y qué hace cada paso

El orden lo impone el grafo de dependencias de Django; no se puede alterar sin romperlo.

| Orden | Migración | Qué hace |
|---|---|---|
| 1 | `sga.0085` | Añade los campos del decreto 44741: `density`, `is_dangerous`, `has_threshold`, `threshold`, `is_pure` |
| 2 | `sga.0086` | Añade `Substance.laboratory` |
| 3 | `sga.0087` | Añade `Substance.features` (M2M a `ObjectFeatures`) |
| 4 | `sga.0088` | Añade `SubstanceCharacteristics.object_related` → el puente con el inventario |
| 5 | `sga.0089` | Añade `img_representation` |
| 6 | **`laboratory.0209`** | **Copia las 2 692 características de `laboratory` a `sga`** |
| 7 | `laboratory.0210` | Añade a `SDSTraceability` la FK nueva hacia SGA, opcional de momento |
| 8 | **`laboratory.0211`** | **Repunta las 2 379 trazas a la característica SGA equivalente** |
| 9 | `laboratory.0212` | Elimina la FK antigua |
| 10 | `laboratory.0213` | Devuelve la FK nueva a **obligatoria**, como lo era antes |
| 11 | `laboratory.0214` | Concede a cada rol y grupo el permiso SGA equivalente al que tenía |
| 12 | `laboratory.0215` | Saca `SDSTraceability` del estado de `laboratory` y reetiqueta su ContentType |
| 13 | `sga.0090` | Crea las características que faltaban para que toda sustancia tenga las suyas |
| 14 | `sga.0091` | Borra los borradores fantasma que dejaba el asistente al abrirse |
| 15 | `sga.0092` | Declara `SDSTraceability` en `sga`, apuntando a la misma tabla física |
| 16 | `sga.0093` | `Substance.laboratory` pasa de uno a varios (`laboratories`) |
| 17 | `auth_and_perms.0032` | Devuelve el acceso al módulo SGA a los roles que gestionan sustancias |
| 18 | `laboratory.0216`–`0217` | Sigla de laboratorio y organización, contador de lote, `shelfobject_code` a 50 |
| 19 | `sga.0094` | Hace explícita la relación sustancia–laboratorio para darle código |
| 20 | `laboratory.0218` | Deriva las siglas del nombre y siembra los contadores |

### Cómo se copian las características (`laboratory.0209`)

La correspondencia es por **objeto de inventario**: cada `SustanceCharacteristics` antigua
apunta a un `Object`, y la fila SGA nueva guarda ese mismo `Object` en `object_related`. Eso
mantiene el vínculo con el inventario sin depender de los pks antiguos.

Puntos de diseño:

- **Se copia todo.** Los 12 campos escalares y los 5 conjuntos M2M (`white_organ`, `h_code`,
  `ue_code`, `nfpa`, `storage_class`). Se comprobó que el modelo SGA es superconjunto del
  antiguo, así que no se pierde ningún dato.
- **`substance` queda nulo.** Estas filas describen objetos de inventario, no sustancias del
  catálogo SGA; ambas cosas conviven en la misma tabla y se distinguen por qué relación tienen
  rellena.
- **Por lotes.** Se recorre con `iterator()` y `prefetch_related`, se insertan las filas con
  `bulk_create` y las relaciones M2M directamente sobre la tabla intermedia. Sin esto la
  migración lanzaba del orden de 48 000 consultas.
- **Se verifica al terminar.** Si el número de filas migradas no iguala al de origen, la
  migración **aborta** y la transacción se deshace entera.

### Cómo se repuntan las trazas (`laboratory.0211`)

Se construye en memoria un único mapa `Object → característica SGA` y se recorren las trazas
haciendo `bulk_update`. Cada traza encuentra su nueva característica a través del `Object` que
compartían la fila antigua y la nueva.

**Aquí está el riesgo real de toda la secuencia**: la migración siguiente elimina la columna de
origen, así que un vínculo que no se migre se pierde para siempre. La versión inicial se
limitaba a imprimir un aviso, que nadie lee en un despliegue desatendido. Ahora **lanza una
excepción y aborta** si queda alguna traza sin pareja. Con los datos actuales no ocurre —las
2 379 se mapean— pero la comprobación existe para que deje de ser una suposición.

### Reversibilidad

La secuencia se puede deshacer con `migrate laboratory 0208`. No lo era: al revertir,
`0212` recreaba la columna vacía y después `0210` intentaba devolverle su restricción
`NOT NULL`, lo que fallaba con `IntegrityError`. Se resolvió haciendo que `0212`, al
revertirse, **repueble la columna** reconstruyendo el vínculo por el `Object` compartido.

El ciclo completo está probado: ida → vuelta → ida, con los mismos resultados las dos veces.

### Los permisos no viajan solos

Un detalle fácil de pasar por alto: los permisos pertenecen a un modelo, así que migrar los
datos no migra los accesos. Un rol con `laboratory.change_sustancecharacteristics` se habría
quedado sin poder editar nada.

- **`laboratory.0214`** concede el permiso SGA equivalente allí donde existía el antiguo, sin
  quitar nada. Sobre datos reales concedió 5 permisos: «Creador de laboratorio» no tenía
  **ninguno** de los cuatro y a «Técnico de Laboratorio» le faltaba `delete`.
- **`laboratory.0215`**, al mover `SDSTraceability` de app, **reetiqueta el `ContentType`
  existente** en lugar de dejar que Django cree permisos nuevos. Así las filas de
  `auth_permission` conservan su identificador y con ellas sus 6 asignaciones a roles y grupos,
  que de otro modo se habrían perdido en silencio.

### Qué se conserva y qué se limpia

- **Se conservan** las 2 692 filas del modelo antiguo, un ciclo más, como respaldo de la
  migración y de su reversa. El modelo queda marcado como obsoleto y retirado del admin para
  que nadie escriba en él. Su eliminación queda programada para la siguiente entrega.
- **Se limpian** 5 borradores de sustancia vacíos, con un filtro deliberadamente estricto: sin
  nombre comercial, en estado borrador y **sin ninguna revisión asociada**. Una sustancia
  enviada a revisión, aunque esté incompleta, es trabajo de alguien y no se toca.
- **Queda una escoba a mano**, `clean_orphan_characteristics`, con `--dry-run`. Como
  `object_related` es `SET_NULL`, borrar un objeto de inventario deja su fila de características
  sin dueño; el comando las localiza y las borra cuando además no cuelgan de ninguna sustancia.
  No se ejecuta en el despliegue: es mantenimiento, no parte de la migración.
- **`Substance.laboratory` pasa de `CASCADE` a `SET_NULL`.** Borrar un laboratorio arrastraba
  consigo las sustancias que lo tuvieran asignado, y son del catálogo de la organización, no
  del laboratorio.

### Verificación tras migrar

```sql
-- correspondencia exacta entre el modelo antiguo y el nuevo
select (select count(*) from laboratory_sustancecharacteristics)
     , (select count(*) from sga_substancecharacteristics where object_related_id is not null);
-- ninguna traza perdió su vínculo
select count(*) from laboratory_sdstraceability where sga_substance_characteristics_id is null;
-- el traslado de app conservó las asignaciones de permisos
select count(*) from auth_and_perms_rol_permissions rp
  join auth_permission p on p.id = rp.permission_id
  join django_content_type ct on ct.id = p.content_type_id
 where ct.model = 'sdstraceability' and ct.app_label = 'sga';
-- toda sustancia tiene características
select count(*) from sga_substance s
  left join sga_substancecharacteristics sc on sc.substance_id = s.id where sc.id is null;
```

En el ensayo sobre la copia de producción: **ida 15 s, vuelta 29 s, reejecución 6 s**.

## Trazabilidad de fichas de seguridad

`SDSTraceability` pasa de `laboratory` a `sga`, conservando su tabla física
(`laboratory_sdstraceability`): renombrarla habría sido cosmético y añadía riesgo.

Cambia además su semántica: de **estado** a **historial**. Antes cada descarga sobrescribía la
traza anterior con `update_or_create`, de modo que solo constaba la ficha vigente. Ahora cada
subida o descarga crea su propia entrada. Los listados de búsqueda muestran la más reciente por
sustancia; la pantalla de verificación muestra el historial completo.

El fichero PDF vive en un solo sitio, `SubstanceCharacteristics.security_sheet`, y la traza
guarda únicamente los metadatos: origen, fecha de revisión, quién verificó y cuándo. El flujo
manual anterior guardaba el archivo dos veces.

### Lectura automática de la ficha

1. La persona sube el PDF en el paso 1. El widget de gentelella lo sube por trozos a su propio
   endpoint y deja un token en el formulario.
2. `sga:upload_sds` resuelve ese token, adjunta el archivo a las características y encola la
   tarea `extract_sds_for_characteristics`.
3. La tarea reutiliza el extractor que ya existía (`_update_substance_from_pdf`), rellena los
   campos reconocidos y crea la entrada de trazabilidad con origen `manual`.
4. El navegador sondea `sga:sds_task_status` y, al terminar, carga los datos en el formulario.

**Subir la ficha nunca falla porque la lectura falle.** La extracción es heurística sobre el
texto del PDF y varía mucho según el fabricante; si no consigue nada, el archivo queda guardado
y los campos se rellenan a mano.

### Qué puede escribir la lectura y qué no

Por ser heurística, la extracción propone pero no manda. La regla es explícita:

- **Desde el asistente solo rellena huecos.** Ni los campos con algo escrito ni los conjuntos
  de códigos ya elegidos se sustituyen. El proceso masivo `update_sds_and_extract_data`, en
  cambio, sí reemplaza: ahí el objetivo es que la ficha descargada mande.
- **El CAS solo se rellena si está vacío**, también en el proceso masivo. Es la llave con la
  que ese proceso localiza la ficha de cada sustancia; sustituirlo por una lectura del PDF
  podría dejarla sin poder actualizarse nunca más.
- **«Precursor» y «lista Seveso» solo se marcan, nunca se desmarcan.** Sus extractores
  devuelven «no» tanto cuando la sustancia no lo es como cuando no encuentran nada, así que
  escribir ese «no» borraba marcas puestas a mano —y el reporte regulatorio de precursores se
  alimenta justo de ese campo.

## Otros arreglos incluidos

- **Reporte de precursores invertido.** El filtro había quedado en `is_precursor=False` al
  migrar, así que el reporte regulatorio listaba justo lo contrario: 2 688 filas equivocadas en
  lugar de las 4 correctas.
- **Características que se guardaban sin enlazar.** El alta desde el módulo de laboratorio
  asignaba `obj` en vez de `object_related`; Django aceptaba el atributo suelto sin error y la
  fila quedaba huérfana.
- **Acceso entre organizaciones.** El envío a revisión y el alta de observaciones no
  comprobaban la organización, y el formulario de revisión aceptaba cualquier organización o
  laboratorio aunque el desplegable solo mostrara los permitidos.
- **Aprobación duplicada.** Aprobar dos veces creaba dos objetos de inventario para la misma
  sustancia; ahora es idempotente y transaccional.
- **Sustancias sin características.** El acceso al `OneToOne` inverso lanzaba excepción en vez
  de devolver vacío, de modo que la tabla de sustancias devolvía error 500 con los datos reales.
- **Restos de la migración en código que no cubrían las pruebas.** Tres sitios seguían usando
  el modelo o el atributo antiguos y fallaban al ejecutarse: el reporte de reactivos por
  organización, que reventaba con cualquier sustancia creada por el asistente nuevo; la
  descarga automática de fichas (`update_sds_for_substance`), que leía `sc.obj`; y los comandos
  `validate_pubchem_sds` y `sync_sds_from_old_db`. Los comandos que aún escribían en la tabla
  obsoleta (`set_mediafiles_names`, `update_sustances_cha`, `sync_susta_charac`) pasan a SGA;
  los dos que leen de la base antigua lo hacen ya por SQL, sin depender de que el modelo
  obsoleto siga declarado.
- **El CAS que se leía y se tiraba.** La extracción lo reconocía en el PDF y lo anunciaba como
  reconocido, pero no estaba en la lista de campos que se guardan.

## Cobertura

828 pruebas en verde, 89 nuevas: el recorrido completo del asistente con sus efectos laterales
(notificaciones, tareas pendientes, observaciones, aprobación), la solicitud para varios
laboratorios y su rastro tras aprobar, la extracción y trazabilidad de fichas —con la política
de escritura descrita arriba—, el traslado de app con sus permisos, los dos reportes que leen
características, y una regresión que fija el filtro de precursores.

Durante la implementación se detectó que **Celery nunca corrió en modo síncrono en las
pruebas**: el ajuste usaba un nombre que Celery no reconoce sin espacio de nombres. También que
las plantillas de correo creadas por migración quedaban destruidas en el entorno de pruebas,
porque `initial_data.json` se carga después y sus identificadores colisionaban.

## Pendiente

- **Traducciones.** Las cadenas nuevas no están en el catálogo. Ejecutar `make messages &&
  make trans` arrastra unas 12 000 líneas de cambios acumulados de antes de esta rama, así que
  conviene hacerlo en un commit propio.
- **Eliminar el modelo antiguo** y sus 2 692 filas, una vez pasado el ciclo de respaldo.
- **Ventana de despliegue.** La secuencia son 34 migraciones; conviene acordar ventana y tener
  el volcado previo a mano, aunque el ensayo tarde menos de medio minuto.
- Reejecutar `load_urlname_permissions` tras desplegar: el comando reconstruye el catálogo de
  permisos entero, y esta entrega renombra y añade claves.
- **Revisar las siglas derivadas.** La migración da sigla a los 142 laboratorios y las 84
  organizaciones sin repetir ninguna, pero salen de una heurística sobre el nombre: conviene que
  cada unidad confirme la suya antes de imprimir etiquetas, porque el código ya no cambia una
  vez emitido.
- **Fusión con `editor-v2`.** Esa rama tiene `sga.0084_recipientsize_laboratory` y esta
  `sga.0084_alter_builderinformation_user_and_more`, **ambas colgando de `0083`**: al integrar
  hará falta una migración de fusión. Además su gestor de etiquetas ya trae
  `RecipientSize.laboratory`, que encaja con los códigos por laboratorio de esta entrega.
