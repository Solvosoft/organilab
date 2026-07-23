import calendar


def add_months(source_date, months):
    """Suma ``months`` meses a ``source_date`` ajustando el día al fin de mes."""
    if source_date is None:
        return None
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return source_date.replace(year=year, month=month, day=day)


def get_iper_config(organization, laboratory=None):
    """Resuelve la IPERConfig aplicable: override por laboratorio si existe, si no
    la de la organización raíz."""
    from risk_management.models import IPERConfig

    if laboratory is not None:
        cfg = IPERConfig.objects.filter(
            laboratory=laboratory, is_active=True
        ).first()
        if cfg:
            return cfg
    root = organization.root if organization is not None else None
    if root is None:
        return None
    return IPERConfig.objects.filter(
        organization=root, laboratory__isnull=True, is_active=True
    ).first()


def compute_risk_level(probability, consequence):
    """Resuelve el nivel de riesgo (entrada Catalog) y su prioridad a partir de la
    probabilidad y consecuencia elegidas, consultando ``IPERRiskMatrix``.

    Devuelve la tupla ``(risk_level_catalog, priority)`` o ``(None, 0)`` si no hay
    celda sembrada para esa combinación.
    """
    from risk_management.iper_defaults import RISK_LEVEL_PRIORITY
    from risk_management.models import IPERRiskMatrix

    if probability is None or consequence is None:
        return None, 0

    cell = IPERRiskMatrix.objects.filter(
        probability=probability, consequence=consequence
    ).select_related("risk_level").first()
    if cell is None:
        return None, 0
    priority = RISK_LEVEL_PRIORITY.get(cell.risk_level.description, 0)
    return cell.risk_level, priority


class PriorityCalculator:

    def operate(self, value):
        dev = False
        right_value = 0 if self.right_value is None else self.right_value
        if self.operation == "<":
            dev = self.left_value < value
        elif self.operation == "<=":
            dev = self.left_value <= value
        elif self.operation == "=":
            dev = self.left_value == value
        elif self.operation == ">":
            dev = self.left_value > value
        elif self.operation == ">=":
            dev = self.left_value >= value
        elif self.operation == "!":
            dev = self.left_value != value
        elif self.operation == "<>":
            dev = self.left_value < value > right_value
        elif self.operation == "=<>=":
            dev = self.left_value <= value >= right_value
        elif self.operation == "=<>=":
            dev = self.left_value <= value >= right_value
        elif self.operation == "<>=":
            dev = self.left_value < value >= right_value
        elif self.operation == "=<>":
            dev = self.left_value <= value > right_value
        elif self.operation == "<<":
            dev = self.left_value < value < right_value
        elif self.operation == "=<<=":
            dev = self.left_value <= value <= right_value
        elif self.operation == "=<<=":
            dev = self.left_value <= value <= right_value
        elif self.operation == "<<=":
            dev = self.left_value < value <= right_value
        elif self.operation == "=<<":
            dev = self.left_value <= value < right_value
        return dev
