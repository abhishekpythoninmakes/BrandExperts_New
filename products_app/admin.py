from django.contrib import admin
from .models import *
from django import forms
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget
# Register your models here.

admin.site.register(CustomUser)
admin.site.register(ParentCategory)
admin.site.register(Category)
class ProductAdminForm(forms.ModelForm):
    product_overview = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    product_specifications = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    installation = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 60}), required=False)  # Normal text field

    class Meta:
        model = Product
        fields = "__all__"

class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm

admin.site.register(Product, ProductAdmin)
admin.site.register(Standard_sizes)
admin.site.register(Product_status)