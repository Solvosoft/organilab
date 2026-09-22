# Plan: Migración de Django 5.2.11 a Django 6.0

## Contexto

Organilab es un sistema de gestión de laboratorios desarrollado con Django 5.2.11. Se requiere evaluar y preparar la migración a Django 6.0 para mantener el proyecto actualizado con las últimas características de seguridad y rendimiento. Esta migración implica revisar tanto el código propio como las dependencias de terceros para garantizar compatibilidad.

---

## Resumen de Impacto

| Categoría | Nivel de Riesgo | Acción Requerida | Estado |
|-----------|-----------------|------------------|--------|
| **Código Organilab** | Bajo | 3 cambios menores | ✅ Completado |
| **Dependencias críticas** | Medio-Alto | 2-3 paquetes requieren actualización | ⚠️ En progreso |
| **Dependencias secundarias** | Bajo | Probablemente compatibles | ⏳ Pendiente verificación |

---

## Parte 1: Cambios Requeridos en el Código de Organilab

### 1.1. ✅ Configuración `USE_L10N` Deprecada (COMPLETADO)

**Archivo:** `src/organilab/settings.py:230`

**Problema:** `USE_L10N` fue eliminado en Django 5.0 (localización siempre está activa). Mantenerlo puede causar warnings o errores.

**Cambio requerido:**
```python
# ELIMINAR esta línea:
USE_L10N = False
```

**Nota:** Verificar que los formatos de fecha/hora funcionen correctamente después del cambio, ya que el sistema usa formatos personalizados en `DATE_INPUT_FORMATS` y `DATETIME_INPUT_FORMATS`.

**Nota importante:** Tenías `USE_L10N = False`, lo que significa que no querías localización de formatos. En Django 5.0+ la localización está siempre activa, así que si necesitas mantener ese comportamiento en formularios específicos, tendrás que usar `localize=False` en cada campo.

---

### 1.2. ✅ Configuración `ADMINS` (COMPLETADO)

**Archivo:** `src/organilab/settings.py:61-63`

**Problema:** Django 6.0 depreca pasar `ADMINS` como lista de tuplas `(name, email)`. Debe ser lista de strings de email.

**Cambio requerido:**
```python
# ANTES:
ADMINS = [
    ("Solvo", "sitio@solvosoft.com"),
]

# DESPUÉS:
ADMINS = ["sitio@solvosoft.com"]
```

---

### 1.3. ✅ Imports desde `django.conf.urls` (COMPLETADO)

**Archivos afectados:**
- `src/reservations_management/urls.py:17`
- `src/laboratory/urls.py:5`

**Problema:** `include` debe importarse desde `django.urls`, no `django.conf.urls`.

**Cambio requerido:**
```python
# ANTES:
from django.conf.urls import include

# DESPUÉS:
from django.urls import include
```

---

### 1.4. `MiddlewareMixin` (BAJA PRIORIDAD)

**Archivo:** `src/auth_and_perms/middleware.py:54`

**Problema:** `ImpostorMiddleware` usa `MiddlewareMixin` que es legacy pero aún soportado.

**Recomendación:** Migrar al patrón moderno `__init__`/`__call__` cuando sea conveniente. No es bloqueante para Django 6.0.

---

### 1.5. `unique_together` Meta Option (ADVERTENCIA FUTURA)

**Archivos afectados:**
- `src/presentation/models.py:186, 217`
- `src/risk_management/models.py:426`

**Problema:** `unique_together` está siendo deprecado en favor de `UniqueConstraint`. No es removido en Django 6.0, pero será en versiones futuras.

**Recomendación futura:**
```python
# ANTES:
class Meta:
    unique_together = [("tutorial", "step_key")]

# DESPUÉS (cuando se migre):
class Meta:
    constraints = [
        models.UniqueConstraint(fields=["tutorial", "step_key"], name="unique_tutorial_step")
    ]
```

---

## Parte 2: Dependencias de Terceros

### 2.1. Dependencias CRÍTICAS que Requieren Actualización

| Paquete | Versión Actual | Requerida para Django 6.0 | Estado |
|---------|----------------|---------------------------|--------|
| **djgentelella** | >=0.6.0 | Verificar con Solvosoft | ⚠️ CRÍTICO - Paquete interno |
| **django-celery-beat** | git (master) | >=2.9.0 | ✅ Actualizado desde git |
| **mozilla-django-oidc** | 4.0.1 | Verificar versión 5.x | ⚠️ Posible actualización |

#### djgentelella (CRÍTICO)

Este es el riesgo más alto de la migración:
- **193 imports** en **101 archivos Python**
- **Alto acoplamiento** en el código
- Provee: GTForm, widgets, serializers, permisos, ObjectManagement

**Acción requerida:** Verificar con el equipo de Solvosoft si djgentelella 0.6.0+ soporta Django 6.0. Si no, la actualización de djgentelella debe hacerse ANTES de migrar Django.

#### django-celery-beat

**Acción:** Actualizar de 2.8.1 a >=2.9.0 en requirements.txt:
```
django-celery-beat>=2.9.0
```

---

### 2.2. Dependencias Probablemente Compatibles

| Paquete | Versión Actual | Compatibilidad Django 6.0 |
|---------|----------------|---------------------------|
| djangorestframework | 3.16.1 | ✅ Confirmado compatible |
| django-tree-queries | (via djgentelella) | ✅ CI incluye Django 6.0 |
| django-otp | 1.7.0 | ⚠️ Verificar PyPI |
| django-filter | 25.1 | ✅ Probablemente compatible |
| django-celery-results | 2.6.0 | ⚠️ Verificar |
| django-cors-headers | 4.6.0 | ✅ Probablemente compatible |

---

### 2.3. Python Version

**Django 6.0 requiere:** Python 3.12, 3.13, o 3.14

**Versión actual del proyecto:** Python 3.13 ✅ Compatible

---

## Parte 3: Cambios Removidos en Django 6.0 (desde deprecaciones 5.0/5.1)

Verificar que el código NO use estos elementos removidos:

| Elemento Removido | Estado en Organilab |
|-------------------|---------------------|
| `DjangoDivFormRenderer` | ✅ No usado |
| `Jinja2DivFormRenderer` | ✅ No usado |
| `format_html()` sin args/kwargs | ✅ No detectado |
| `FORMS_URLFIELD_ASSUME_HTTPS` setting | ✅ No usado |
| `ChoicesMeta` alias | ✅ No usado |
| `Prefetch.get_current_queryset()` | ✅ No usado |
| `ModelAdmin.log_deletion()` | ✅ No usado |
| `LogEntryManager.log_action()` | ✅ No usado |
| Argumentos posicionales en `Model.save()` | ✅ No detectado |
| `django.utils.itercompat` | ✅ No usado |

---

## Parte 4: Plan de Implementación

### Fase 1: Preparación (antes de actualizar Django)

1. ⚠️ **Actualizar djgentelella** (si hay nueva versión compatible)
2. ✅ **Actualizar django-celery-beat** a >=2.9.0 — Actualizado desde git master
3. ⏳ **Verificar mozilla-django-oidc** compatibilidad

### Fase 2: Cambios de Código ✅ COMPLETADO

1. ✅ Remover `USE_L10N` de `src/organilab/settings.py`
2. ✅ Actualizar `ADMINS` en `src/organilab/settings.py`
3. ✅ Actualizar imports de `include` en archivos de URLs

### Fase 3: Actualización de Django ✅ COMPLETADO

```bash
# requirements.txt actualizado:
django===6.0
django-celery-beat @ git+https://github.com/celery/django-celery-beat.git
```

### Fase 4: Verificación

1. Ejecutar migraciones: `python manage.py migrate`
2. Ejecutar tests: `make test`
3. Verificar formatos de fecha/hora funcionan correctamente
4. Probar autenticación OIDC si está habilitada
5. Verificar tareas de Celery funcionan

---

## Archivos Modificados

| Archivo | Cambio | Estado |
|---------|--------|--------|
| `src/organilab/settings.py` | Eliminar USE_L10N, Actualizar ADMINS | ✅ Completado |
| `src/reservations_management/urls.py` | Actualizar import | ✅ Completado |
| `src/laboratory/urls.py` | Actualizar import | ✅ Completado |
| `requirements.txt` | Actualizar django y django-celery-beat | ✅ Completado |

---

## Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| djgentelella no compatible | Media | Crítico | Coordinar con Solvosoft antes de migrar |
| Cambios en formatos de fecha | Baja | Medio | Probar exhaustivamente formularios |
| Problemas con OIDC | Baja | Medio | Probar flujo de login completo |

---

## Fuentes Consultadas

- [Django 6.0 Release Notes](https://docs.djangoproject.com/en/6.0/releases/6.0/)
- [Django Deprecation Timeline](https://docs.djangoproject.com/en/dev/internals/deprecation/)
- [django-celery-beat Issue #977](https://github.com/celery/django-celery-beat/issues/977)
- [Django REST Framework Release Notes](https://www.django-rest-framework.org/community/release-notes/)
- [django-tree-queries Documentation](https://django-tree-queries.readthedocs.io/)
- [Solvosoft django-gentelella-widgets GitHub](https://github.com/Solvosoft/django-gentelella-widgets)
