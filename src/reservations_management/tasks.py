import importlib
import logging

from django.conf import settings

from .models import ReservedProducts

app = importlib.import_module(settings.CELERY_MODULE).app
logger = logging.getLogger("organilab")


@app.task
def decrease_stock(reserved_product):
    """
    Decrease the stock quantity of one reserved product
    reserved_product is an instancw of ReservedProducts
    """
    if not isinstance(reserved_product, ReservedProducts):
        try:
            reserved_product = ReservedProducts.objects.get(pk=reserved_product)
        except Exception as e:
            logger.error("Decrease stock", exc_info=e)
            return

    reserved_product.shelf_object.quantity -= reserved_product.amount_required
    reserved_product.shelf_object.save()
