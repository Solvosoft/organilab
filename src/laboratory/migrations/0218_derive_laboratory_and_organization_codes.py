from django.db import migrations

from sga.substance_codes import parse_lot_code, suggest_code


def _assign(model, db_alias):
    """Da sigla a cada fila que no la tenga, sin repetir ninguna."""
    tomadas = set(
        model.objects.using(db_alias)
        .exclude(code=None)
        .exclude(code="")
        .values_list("code", flat=True)
    )
    asignadas = 0
    sin_sigla = []

    for pk, name in (
        model.objects.using(db_alias)
        .filter(code__isnull=True)
        .order_by("pk")
        .values_list("pk", "name")
    ):
        code = suggest_code(name, tomadas)
        if not code:
            sin_sigla.append(pk)
            continue
        model.objects.using(db_alias).filter(pk=pk).update(code=code)
        tomadas.add(code)
        asignadas += 1

    return asignadas, sin_sigla


def derive_codes(apps, schema_editor):
    """Deriva la sigla de laboratorios y organizaciones a partir del nombre.

    Sin sigla no hay código posible, así que se derivan todas para que el módulo
    quede operativo sin depender de un trabajo manual previo unidad por unidad.
    Son una propuesta razonable, no la última palabra: quedan editables, y quien
    conoce la unidad puede corregir la suya.

    El criterio prioriza la sigla que el propio nombre declare entre paréntesis
    y, si no la hay, compone las iniciales de las palabras que distinguen a esa
    unidad, descartando los genéricos que muchos nombres comparten.
    """
    db_alias = schema_editor.connection.alias

    for etiqueta in ("Laboratory", "OrganizationStructure"):
        model = apps.get_model("laboratory", etiqueta)
        asignadas, sin_sigla = _assign(model, db_alias)
        if asignadas:
            print(f"\nDerived {asignadas} {etiqueta} codes")
        if sin_sigla:
            print(
                f"WARNING: {len(sin_sigla)} {etiqueta} sin sigla derivable "
                f"(nombre sin letras): {sin_sigla[:10]}"
            )


def seed_counters(apps, schema_editor):
    """Siembra los contadores de lote con los códigos que ya existan.

    Un consecutivo ya impreso en una etiqueta no puede volver a emitirse. Si la
    base llega con códigos que siguen la fórmula —porque la migración se
    reejecuta o porque los datos vienen de otra instancia— el contador debe
    arrancar por encima del mayor que ya exista, no en cero.
    """
    db_alias = schema_editor.connection.alias
    ShelfObject = apps.get_model("laboratory", "ShelfObject")
    Counter = apps.get_model("laboratory", "ShelfObjectCodeCounter")
    SubstanceLaboratory = apps.get_model("sga", "SubstanceLaboratory")

    por_codigo = {
        code: pk
        for pk, code in SubstanceLaboratory.objects.using(db_alias)
        .exclude(code=None)
        .values_list("pk", "code")
    }
    if not por_codigo:
        return

    maximos = {}
    queryset = (
        ShelfObject.objects.using(db_alias)
        .exclude(shelfobject_code=None)
        .exclude(shelfobject_code="")
        .values_list("shelfobject_code", flat=True)
    )
    for code in queryset.iterator(chunk_size=500):
        datos = parse_lot_code(code)
        if not datos:
            continue
        prefijo = code.rsplit("-", 3)[0]
        enlace_pk = por_codigo.get(prefijo)
        if enlace_pk is None:
            continue
        clave = (enlace_pk, datos["year"], datos["month"])
        maximos[clave] = max(maximos.get(clave, 0), datos["counter"])

    for (enlace_pk, year, month), contador in maximos.items():
        Counter.objects.using(db_alias).update_or_create(
            substance_laboratory_id=enlace_pk,
            year=year,
            month=month,
            defaults={"counter": contador},
        )

    if maximos:
        print(f"\nSeeded {len(maximos)} shelf object code counters")


def clear_codes(apps, schema_editor):
    """Al revertir se retiran las siglas derivadas y los contadores sembrados."""
    db_alias = schema_editor.connection.alias
    for etiqueta in ("Laboratory", "OrganizationStructure"):
        apps.get_model("laboratory", etiqueta).objects.using(db_alias).update(code=None)
    apps.get_model("laboratory", "ShelfObjectCodeCounter").objects.using(
        db_alias
    ).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0217_shelfobjectcodecounter_substance_laboratory_and_more"),
        ("sga", "0094_substancelaboratory_alter_substance_laboratories"),
    ]

    operations = [
        migrations.RunPython(derive_codes, reverse_code=clear_codes),
        migrations.RunPython(seed_counters, reverse_code=migrations.RunPython.noop),
    ]
