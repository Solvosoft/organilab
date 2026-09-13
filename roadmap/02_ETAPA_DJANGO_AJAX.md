# Etapa 2 — django_ajax: dependencia asumida (salida diferida a la etapa 10)

**Estado: HECHA (2026-08-29), con enfoque ajustado.**

## Qué se decidió y por qué

Al medir la superficie real, "portar 3 vistas" era en realidad: 3 funciones `@ajax` + **7 CBVs
`AJAXMixin`** (`ShelfCreate/Edit`, `ShelfObjectCreate/Edit/SearchUpdate/Delete/Detail`) + ~10
templates con `data-ajax`/`data-ajax-submit` + 6 callbacks `processResponse*` en JS. Todo ese flujo
(editor de mobiliario/estantes con modales) es exactamente lo que la etapa 10 va a rehacer con
`ObjectCRUD`/`BaseInlineObjectManagement`. Reescribirlo dos veces no tiene sentido.

**Enfoque ejecutado:** organilab asume la dependencia directamente mientras esas pantallas existan
en su forma actual:

1. `requirements.txt`: `djangoajax==3.3` declarado explícito (el paquete Python funciona con
   Django 5.2 — es lo que corre hoy; NO trae estáticos).
2. Los 2 JS del plugin (que los aportaba djgentelella y 0.6.0 borró) quedaron **vendorizados** en
   `src/presentation/static/django_ajax/js/jquery.ajax{,-plugin}.min.js` (extraídos del tag
   v0.5.9). Misma ruta estática → `base.html` no cambia; `findstatic` confirma que la copia de
   `presentation` gana (INSTALLED_APPS: presentation:76 < djgentelella:92).
3. `INSTALLED_APPS` conserva `"django_ajax"`.

## Eliminación definitiva (mover a etapa 10)

Cuando las pantallas de mobiliario/estantes se modernicen con ObjectCRUD: quitar `djangoajax` de
requirements, borrar `src/presentation/static/django_ajax/`, quitar los `<script>` de
`base.html:36-37`, quitar `"django_ajax"` de INSTALLED_APPS, y eliminar los `data-ajax`/
`processResponse*` de los templates/JS listados arriba.

## Contrato del plugin (para la etapa 10)

Envoltorio servidor: `{status, statusText, content}`; 301/302 → redirect a `content`. Cliente:
`content.fragments` → `replaceWith`, `content['inner-fragments']` → `.html()` (evalúa `<script>`),
`append-/prepend-fragments`; anchors `[data-ajax]` interceptados, `data-success="fn"` recibe
`response.content`; forms `[data-ajax-submit]` serializados, su `data-success` recibe la respuesta
completa como `{content: respuesta}`. Helpers globales: `ajax()`, `ajaxGet`, `ajaxPost`,
`ajaxMethod` (con CSRF automático).
