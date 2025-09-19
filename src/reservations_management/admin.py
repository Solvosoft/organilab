from django.contrib import admin

from reservations_management.models import (
    Reservations,
    ReservedProducts,
    ReservationRange,
    ReservationTasks,
)

admin.site.register(Reservations)
admin.site.register(ReservedProducts)
admin.site.register(ReservationRange)
admin.site.register(ReservationTasks)
