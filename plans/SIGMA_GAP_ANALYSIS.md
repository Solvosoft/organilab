# SIGMA vs. Organilab — índice de lo que se decidió incorporar

> **Qué es esto.** Resumen del análisis entre los *Requerimientos Mínimos del SIGMA* (MOPT, junio
> 2026) y Organilab. La tabla requisito por requisito está en git (antes del 2026-09-16).
>
> **Estado (2026-09-16):** consumos (salvo importación) y la plataforma C/D/E están en la rama
> `regenteambiental`; programas de gestión sigue sin código — ver cada plan.

---

## 1. Qué se toma de SIGMA

| # | Bloque | Hueco que cubre en Organilab | Plan | Estado |
|---|--------|------------------------------|------|--------|
| 1 | Plataforma: bitácora exportable con antes→después, justificación, parámetros, notificaciones y alertas configurables, FAQ/video/"Acerca de", expiración de sesión | Se **captura** auditoría pero casi no se **expone**; umbrales y correos hardcodeados | [`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md) | C, D y E hechos; A parcial |
| 2 | Programas de gestión → planes anuales → acciones → actividades → seguimiento con % y evidencias; avance y ranking por dependencia | Los hallazgos (IPER, incidentes, límites) no tienen seguimiento planificado | [`MANAGEMENT_PLANS_PLAN.md`](MANAGEMENT_PLANS_PLAN.md) | No iniciado |
| 3 | Consumos y residuos + indicadores normalizados + comparaciones + alertas por consumo atípico | No hay dónde registrar consumos; los denominadores (`Buildings.area`, `Structure.area`, jornadas) ya existen | [`ENVIRONMENT_PLAN.md`](ENVIRONMENT_PLAN.md) | Hecho salvo importación masiva |

**Orden recomendado:** plataforma → programas → consumos (plataforma es transversal y barata;
programas es el esqueleto del que cuelgan los consumos; consumos es el más caro y el que más depende
de decisiones de negocio).

## 2. Qué **no** se incorpora

Portal de Aplicaciones del MOPT (ya hay OIDC y firma digital) · integraciones SPP/CITEC/SIOR (se
conserva solo el patrón import + captura manual; el árbol org sustituye a SIOR) · catálogo NIS literal
(se generaliza a "punto de medición") · plantillas de residuos de un ente externo · video como único
mecanismo de ayuda (se agrega a `Tutorial`).

## 3. Principios a copiar

1. Cambios con dependientes exigen justificación y avisan.
2. Histórico con valor anterior → nuevo → usuario → justificación.
3. Todo reporte se exporta y se grafica (`REPORT_FORMS`).
4. Indicadores normalizados para comparar unidades desiguales.
5. Catálogos como datos, no código.

## 4. Decisiones abiertas

- **Consumos por laboratorio, por edificio o por punto de medición** (el plan propone punto asociable
  a ambos; falta definir el camino corto). La decisión de negocio más importante.
- Apps nuevas (`environment`, `management_plans`) vs. extender `risk_management` — recomendación: apps nuevas.
- Carga del usuario final: los módulos nuevos deben entrar por `PendingTask`, no como "una pantalla más".
