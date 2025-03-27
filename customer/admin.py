from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Customer, WarrantyRegistration, ClaimWarranty, Customer_Address,
    Cart, CartItem, Order,CustomerDesign, OTPRecord ,PasswordResetSession , Client_user
)
from django.contrib.auth.models import Group

# Unregister the default Group model


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_link', 'customer_name', 'customer_email', 'total_amount',
        'status', 'ordered_date'
    )
    list_filter = ('status', 'ordered_date')
    search_fields = ('id', 'customer__user__username', 'customer__user__email')
    readonly_fields = (
        'id', 'ordered_date', 'cart_id', 'cart_details',
        'cart_items_display', 'customer_details', 'address_details'
    )
    fieldsets = (
        ('Order Information', {
            'fields': (
                'id', 'ordered_date', 'delivered_date', 'status', 'cart_id',
                'cart_details', 'cart_items_display'
            )
        }),
        ('Payment Information', {
            'fields': (
                'amount', 'payment_method', 'payment_status', 'transaction_id'
            )
        }),
        ('Customer Information', {
            'fields': ('customer_details', 'address_details',)
        }),
        ('Site Visit', {
            'fields': ('site_visit', 'site_visit_fee')
        }),
        ('VAT', {
            'fields': ('vat_percentage', 'vat_amount')
        }),
    )

    def order_link(self, obj):
        link = reverse("admin:customer_order_change", args=(obj.id,))
        return format_html(
            '<a href="{}">Order #{} - {}</a>', link, obj.id,
            obj.customer.user.get_full_name()
        )
    order_link.short_description = 'Order'

    def customer_name(self, obj):
        return obj.customer.user.get_full_name() if obj.customer.user else "Unknown Customer"
    customer_name.short_description = 'Customer Name'

    def customer_email(self, obj):
        return obj.customer.user.email if obj.customer.user else "No Email"
    customer_email.short_description = 'Customer Email'

    def total_amount(self, obj):
        return obj.amount
    total_amount.short_description = 'Total Amount'

    def cart_id(self, obj):
        return obj.cart.id if obj.cart else "No Cart"
    cart_id.short_description = 'Cart ID'

    def cart_details(self, obj):
        if obj.cart:
            cart_details = []
            cart_details.append(f"Status: {obj.cart.status}")
            cart_details.append(f"Created At: {obj.cart.created_at}")
            cart_details.append(f"Higher Designer: {obj.cart.higher_designer}")
            cart_details.append(f"Site Visit: {obj.cart.site_visit}")
            return format_html("<br>".join(cart_details))
        return "No Cart"
    cart_details.short_description = 'Cart Details'

    def cart_items_display(self, obj):
        if obj.cart:
            items = []
            for item in obj.cart.items.all():
                image_tag = format_html(
                    '<img src="{}" width="50" height="50">', item.design_image
                )
                cart_item_link = reverse(
                    "admin:customer_cartitem_change", args=(item.id,)
                )
                items.append(format_html(
                    '<a href="{}">{} - {}</a>', cart_item_link, image_tag,
                    item.product.name
                ))
            return format_html("<br>".join(items))
        return "No Cart Items"
    cart_items_display.short_description = 'Cart Items'

    def customer_details(self, obj):
        customer = obj.customer
        if customer and customer.user:
            link = reverse("admin:customer_customer_change", args=(customer.id,))
            full_name = customer.user.get_full_name()
            email = customer.user.email
            mobile = customer.mobile if customer.mobile else "No Mobile"
            return format_html(
                '<a href="{}">{} ({})</a> - {} - {}',
                link, full_name, customer.user.username, email, mobile
            )
        return "Unknown Customer"
    customer_details.short_description = 'Customer Details'

    def address_details(self, obj):
        address = obj.address
        if address:
            details = []
            details.append(f"Company: {address.company_name}")
            details.append(f"Extension: {address.ext}")
            details.append(f"Address Line 1: {address.address_line1}")
            details.append(f"Address Line 2: {address.address_line2}")
            details.append(f"Country: {address.country}")
            details.append(f"City: {address.city}")
            details.append(f"State: {address.state}")
            details.append(f"Zip Code: {address.zip_code}")
            return format_html("<br>".join(details))
        return "No Address"
    address_details.short_description = 'Customer Address'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'customer__user', 'cart', 'address'
        )

# Register models
admin.site.register(Customer)
admin.site.register(WarrantyRegistration)
admin.site.register(ClaimWarranty)
admin.site.register(Customer_Address)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(OTPRecord)


@admin.register(CustomerDesign)
class CustomerDesignAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_id', 'product_name', 'product_max_width', 'product_max_height', 'quantity', 'created_at')
    list_filter = ('customer', 'product_name', 'created_at')
    search_fields = ('customer__user__username', 'anonymous_uuid', 'product_name')
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        ("Customer & Design Info", {
            "fields": ("id", "customer", "anonymous_uuid", "created_at"),
        }),
        ("Product Details", {
            "fields": ("product_name", "product_max_width", "product_max_height", "quantity"),
        }),
        ("Design Data", {
            "fields": ("design_data",),
        }),
    )

    def customer_id(self, obj):
        """Return the customer's ID if available."""
        return obj.customer.id if obj.customer else "Anonymous"

    customer_id.short_description = "Customer ID"


admin.site.register(PasswordResetSession)


# @admin.register(Client_user)
# class ClientUserAdmin(admin.ModelAdmin):
#     # Fields to display in the list view
#     list_display = ('name', 'email_link', 'mobile_link', 'user_username', 'status')
#
#     # Fields to filter by in the right sidebar
#     list_filter = ('status', 'user')
#
#     # Fields to search by in the search bar
#     search_fields = ('name', 'email', 'mobile', 'user__username')
#
#     # Fields to group in the edit form
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('name', 'email', 'mobile')
#         }),
#         ('User Information', {
#             'fields': ('user',),
#             'description': 'Link this client to an existing user (optional).'
#         }),
#         ('Status', {
#             'fields': ('status',),
#             'description': 'Set the status of the client.'
#         }),
#     )
#
#     # Custom method to display linked user's username
#     def user_username(self, obj):
#         return obj.user.username if obj.user else "No User Linked"
#
#     user_username.short_description = 'Linked User'
#
#     # Custom method to display email as a clickable link
#     def email_link(self, obj):
#         if obj.email:
#             return mark_safe(f'<a href="mailto:{obj.email}">{obj.email}</a>')
#         return "No Email"
#
#     email_link.short_description = 'Email'
#
#     # Custom method to display mobile as a clickable link
#     def mobile_link(self, obj):
#         if obj.mobile:
#             return mark_safe(f'<a href="tel:{obj.mobile}">{obj.mobile}</a>')
#         return "No Mobile"
#
#     mobile_link.short_description = 'Mobile'
