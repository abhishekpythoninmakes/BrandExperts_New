from django.contrib import admin
from .models import *
from django import forms
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget
# Register your models here.

admin.site.site_header = "BrandExperts Admin Panel"
admin.site.site_title = "BrandExperts Admin Panel"
admin.site.index_title = "Welcome to BrandExperts Admin Dashboard"




@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    search_fields = ['email', 'username', 'first_name', 'last_name'] 

@admin.register(ParentCategory)
class ParentCategoryAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['category_name', 'description']


class ProductAdminForm(forms.ModelForm):
    product_overview = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    product_specifications = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    installation = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 60}), required=False)  # Normal text field

    class Meta:
        model = Product
        fields = "__all__"

# Custom Product Admin
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'get_categories', 'get_parent_categories', 'size', 'price', 'status')
    search_fields = ('name', 'categories__category_name', 'categories__parent_categories__name', 'size', 'description')

    def get_categories(self, obj):
        return ", ".join([category.category_name for category in obj.categories.all()])
    get_categories.short_description = 'Categories'

    def get_parent_categories(self, obj):
        parent_categories = set()
        for category in obj.categories.all():
            parent_categories.update(category.parent_categories.all())
        return ", ".join([parent.name for parent in parent_categories])
    get_parent_categories.short_description = 'Parent Categories'

admin.site.register(Product, ProductAdmin)
admin.site.register(Standard_sizes)
admin.site.register(Product_status)
admin.site.register(Warranty_plan)
admin.site.register(VAT)
admin.site.register(Higher_designer)
class ProductOfferSliderAdmin(admin.ModelAdmin):
    list_display = ('short_offer_details', 'date')
    search_fields = ('offer_details',)
    ordering = ('-date',)

admin.site.register(Product_Offer_slider, ProductOfferSliderAdmin)

admin.site.register(Designer_rate)