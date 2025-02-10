from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Product)
admin.site.register(Product_overview)
admin.site.register(Product_specifications)
admin.site.register(Product_installation)
admin.site.register(Installation_steps)