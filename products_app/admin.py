from django.contrib import admin
from django.http import JsonResponse

from .models import *
from django import forms
from django.utils.html import format_html
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.urls import path
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
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 60}), required=False)

    class Meta:
        model = Product
        fields = "__all__"

# Inline for Standard Sizes
class StandardSizesInline(admin.TabularInline):
    model = Standard_sizes
    extra = 1  # Number of empty forms to display
    fields = ('width', 'height', 'unit', 'standard_sizes')
    readonly_fields = ('standard_sizes',)  # Auto-generated field
    verbose_name_plural = "Standard Sizes"

# Custom Product Admin
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    inlines = [StandardSizesInline]  # Add inline for standard sizes
    list_display = (
        'name',
        'image1_preview',
        'price',
        'status',
        'get_categories',
        'get_parent_categories',
        'size',
        'allow_direct_add_to_cart'
    )
    list_filter = ('status', 'categories', 'size', 'allow_direct_add_to_cart')  # Enhanced filters
    search_fields = ('name', 'categories__category_name', 'categories__parent_categories__name', 'size', 'description')
    ordering = ('-id',)  # Order by newest first
    list_per_page = 20  # Pagination
    readonly_fields = ('image1_preview', 'image2_preview', 'image3_preview', 'image4_preview')  # Image previews
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'categories', 'status', 'price', 'size', 'allow_direct_add_to_cart')
        }),
        ('Dimensions', {
            'fields': ('min_width', 'max_width', 'min_height', 'max_height')
        }),
        ('Product Details', {
            'fields': ('product_overview', 'product_specifications', 'installation')
        }),
        ('Images', {
            'fields': ('image1', 'image1_preview', 'image2', 'image2_preview', 'image3', 'image3_preview', 'image4', 'image4_preview')
        }),
        ('External Links', {
            'fields': ('amazon_url',)
        }),
    )

    # Image Previews
    def image1_preview(self, obj):
        if obj.image1:
            return format_html('<img src="{}" width="80" height="50" style="border-radius: 5px; object-fit: cover;" />', obj.image1)
        return "No Image"

    def image2_preview(self, obj):
        if obj.image2:
            return format_html('<img src="{}" width="80" height="50" style="border-radius: 5px; object-fit: cover;" />', obj.image2)
        return "No Image"

    def image3_preview(self, obj):
        if obj.image3:
            return format_html('<img src="{}" width="80" height="50" style="border-radius: 5px; object-fit: cover;" />', obj.image3)
        return "No Image"

    def image4_preview(self, obj):
        if obj.image4:
            return format_html('<img src="{}" width="80" height="50" style="border-radius: 5px; object-fit: cover;" />', obj.image4)
        return "No Image"

    image1_preview.short_description = "Image 1 Preview"
    image2_preview.short_description = "Image 2 Preview"
    image3_preview.short_description = "Image 3 Preview"
    image4_preview.short_description = "Image 4 Preview"

    # Get Categories
    def get_categories(self, obj):
        return ", ".join([category.category_name for category in obj.categories.all()])

    get_categories.short_description = 'Categories'

    # Get Parent Categories
    def get_parent_categories(self, obj):
        parent_categories = set()
        for category in obj.categories.all():
            parent_categories.update(category.parent_categories.all())
        return ", ".join([parent.name for parent in parent_categories])

    get_parent_categories.short_description = 'Parent Categories'

    class Media:
        js = ('admin/js/product_admin.js',)  # Add custom JavaScript for lazy loading images

# Register the model with the customized admin class
admin.site.register(Product, ProductAdmin)


class StandardSizesAdmin(admin.ModelAdmin):
    change_form_template = 'admin/products_app/standard_sizes/change_form.html'
    list_display = ('product', 'standard_sizes', 'width', 'height','unit')
    readonly_fields = ('product_details',)

    fieldsets = (
        (None, {
            'fields': ('product', 'width', 'height','unit', 'product_details')
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'get-product-details/',
                self.admin_site.admin_view(self.get_product_details),
                name='get_product_details'
            ),
        ]
        return custom_urls + urls

    def get_product_details(self, request):
        product_id = request.GET.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
            return JsonResponse({
                'size': product.size,
                'min_width': float(product.min_width),
                'max_width': float(product.max_width),
                'min_height': float(product.min_height),
                'max_height': float(product.max_height),
            })
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def product_details(self, obj):
        if obj.product:
            return format_html(
                'Unit: {}<br>'
                'Min Width: {} {}<br>'
                'Max Width: {} {}<br>'
                'Min Height: {} {}<br>'
                'Max Height: {} {}',
                obj.product.size,
                obj.product.min_width, obj.product.size,
                obj.product.max_width, obj.product.size,
                obj.product.min_height, obj.product.size,
                obj.product.max_height, obj.product.size,
            )
        return "No product selected"

    product_details.short_description = 'Product Details'
    product_details.allow_tags = True

    class Media:
        js = ('admin/js/product_details.js',)
admin.site.register(Standard_sizes, StandardSizesAdmin)

admin.site.register(Product_status)
admin.site.register(Warranty_plan)
admin.site.register(VAT)

class ProductOfferSliderAdmin(admin.ModelAdmin):
    list_display = ('short_offer_details', 'date')
    search_fields = ('offer_details',)
    ordering = ('-date',)

admin.site.register(Product_Offer_slider, ProductOfferSliderAdmin)

admin.site.register(Designer_rate)


class BannerImageAdminForm(forms.ModelForm):
    class Meta:
        model = Banner_Image
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = '<span class="custom-help-text">The uploaded image should have a width of <b>1250px</b> and a height of <b>699px</b>.</span>'


class BannerImageAdmin(admin.ModelAdmin):
    form = BannerImageAdminForm  # Link the custom form
    list_display = ('name', 'image_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name',)
    ordering = ('-created_at',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" height="50" style="border-radius: 5px;" />', obj.image)
        return "No Image"

    image_preview.short_description = "Image Preview"

admin.site.register(Banner_Image, BannerImageAdmin)



class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'occupation', 'image_preview', 'rating', 'created_at')  # Display relevant fields
    list_filter = ('rating', 'created_at')  # Add filtering options
    search_fields = ('name', 'occupation', 'description')  # Enable search
    ordering = ('-created_at',)  # Order by newest first

    def image_preview(self, obj):
        if obj.image:  # Check if image URL exists
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px;" />', obj.image)
        return "No Image"

    image_preview.short_description = "Image Preview"  # Column header in admin panel


# Register the model with the custom admin class
admin.site.register(Testimonials, TestimonialAdmin)


class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ('amount', 'created_at')
    readonly_fields = ('created_at',)  # Prevent editing of created_at field

    def has_add_permission(self, request):
        """Prevent adding a new record if one already exists."""
        if site_visit.objects.exists():
            if not request.session.get("only_one_warning_shown", False):  # Use session to track warning
                messages.error(request, mark_safe("<b>Only one site visit record is allowed.</b> You can only edit the existing one."))
                request.session["only_one_warning_shown"] = True  # Store flag in session
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the existing object."""
        return False

admin.site.register(site_visit, SiteVisitAdmin)