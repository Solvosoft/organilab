
from django.conf import settings
import importlib
import os

from .models import ReservedProducts


app = importlib.import_module(settings.CELERY_MODULE).app


@app.task
def decrease_stock(reserved_product):
    """
    Decrease the stock quantity of one reserved product
    obj puede ser un pk o una instancia ReservedProducts
    """
    
    if not isinstance(reserved_product, ReservedProducts):
        try:
            reserved_product = ReservedProducts.objects.get(pk=reserved_product)
        except:
            return

    reserved_product.shelf_object.quantity += reserved_product.amount_required
    reserved_product.save()
