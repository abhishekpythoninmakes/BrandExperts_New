from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Customer, WarrantyRegistration, ClaimWarranty, Customer_Address,
    Cart, CartItem, Order,CustomerDesign, OTPRecord ,PasswordResetSession , RequestedEmailUsers
)
from django.contrib.auth.models import Group

# Unregister the default Group model


from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Order, CartItem


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_link', 'customer_name', 'customer_email', 'total_amount',
        'status', 'ordered_date'
    )
    list_filter = ('status', 'ordered_date', 'payment_method', 'payment_status')
    search_fields = ('id', 'customer__user__username', 'customer__user__email', 'transaction_id')
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
                # Main item information
                image_tag = format_html(
                    '<img src="{}" width="50" height="50">', item.design_image
                ) if item.design_image else "No Image"

                cart_item_link = reverse(
                    "admin:customer_cartitem_change", args=(item.id,)
                )

                # Base item info
                item_info = [
                    format_html(
                        '<strong><a href="{}">{} - {}</a></strong>',
                        cart_item_link, image_tag, item.product.name
                    ),
                    format_html(
                        'Dimensions: {} {} x {} {}',
                        item.custom_width, item.size_unit,
                        item.custom_height, item.size_unit
                    ),
                    format_html('Price: {:.2f}', item.price),
                    format_html('Quantity: {}', item.quantity),
                    format_html('Total: {:.2f}', item.total_price)
                ]

                # Thickness info
                if item.thickness_object_id and item.thickness_content_type:
                    thickness_obj = item.thickness_content_type.get_object_for_this_type(id=item.thickness_object_id)
                    item_info.append(format_html(
                        '<strong>Thickness:</strong> {} ({} {})',
                        thickness_obj.size,
                        thickness_obj.price_percentage if hasattr(thickness_obj, 'price_percentage') else '',
                        thickness_obj.price
                    ))

                # Delivery info
                if item.delivery_object_id and item.delivery_content_type:
                    delivery_obj = item.delivery_content_type.get_object_for_this_type(id=item.delivery_object_id)
                    item_info.append(format_html(
                        '<strong>Delivery:</strong> {} ({}% / {})',
                        delivery_obj.name,
                        delivery_obj.price_percentage or '0',
                        delivery_obj.price_decimal or '0'
                    ))

                # Installation info
                if item.installation_object_id and item.installation_content_type:
                    installation_obj = item.installation_content_type.get_object_for_this_type(
                        id=item.installation_object_id)
                    item_info.append(format_html(
                        '<strong>Installation:</strong> {} ({} days - {}% / {})',
                        installation_obj.name,
                        installation_obj.days,
                        installation_obj.price_percentage or '0',
                        installation_obj.price_decimal or '0'
                    ))

                # Turnaround time info
                if item.turnaround_object_id and item.turnaround_content_type:
                    turnaround_obj = item.turnaround_content_type.get_object_for_this_type(id=item.turnaround_object_id)
                    item_info.append(format_html(
                        '<strong>Turnaround Time:</strong> {} ({}% / {})',
                        turnaround_obj.name,
                        turnaround_obj.price_percentage or '0',
                        turnaround_obj.price_decimal or '0'
                    ))

                # Distance info
                if item.distance_object_id and item.distance_content_type:
                    distance_obj = item.distance_content_type.get_object_for_this_type(id=item.distance_object_id)
                    item_info.append(format_html(
                        '<strong>Distance:</strong> {} ({}% / {})',
                        distance_obj.km,
                        distance_obj.price_percentage or '0',
                        distance_obj.price_decimal or '0'
                    ))

                # Additional info
                if item.hire_designer:
                    item_info.append(format_html(
                        '<strong>Hire Designer:</strong> {} ({} {})',
                        item.hire_designer.get_rate_type_display(),
                        item.hire_designer.hours,
                        item.hire_designer.amount
                    ))

                if item.design_description:
                    item_info.append(format_html(
                        '<strong>Design Description:</strong> {}',
                        item.design_description[:100] + ('...' if len(item.design_description) > 100 else '')
                    ))

                # Add Smart Glass info if applicable
                if item.is_smart:
                    item_info.append(format_html('<strong>Smart Glass:</strong> Yes'))

                # Add a divider between items
                items.append(
                    format_html('<div style="margin-bottom: 15px;">{}</div>', format_html('<br>'.join(item_info))))

            return format_html('<div style="max-height: 400px; overflow-y: auto;">{}</div>',
                               format_html(''.join(items)))
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
        ).prefetch_related(
            'cart__items',
            'cart__items__product'
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
