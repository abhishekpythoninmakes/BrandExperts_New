from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Customer)
admin.site.register(WarrantyRegistration)
admin.site.register(ClaimWarranty)
admin.site.register(Customer_Address)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
