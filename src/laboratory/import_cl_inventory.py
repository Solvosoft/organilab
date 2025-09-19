import csv
from laboratory.models import CLInventory


def import_cl_inventory():
    with open("laboratory/cl_inventory.csv", "r") as inventory_csv:
        reader = csv.DictReader(inventory_csv)
        for row in reader:
            kwargs = {
                "name": row.get("name"),
                "cas_id_number": row.get("cas_id_number"),
                "url": row.get("url"),
            }
            CLInventory.objects.create(**kwargs)
