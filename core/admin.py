from django.contrib import admin

from core.models import Appointment, Barber, Customer, Service

# Register your models here.

admin.site.register(Customer)
admin.site.register(Barber)
admin.site.register(Service)
admin.site.register(Appointment)