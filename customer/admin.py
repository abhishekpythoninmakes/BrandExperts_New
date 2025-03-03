from django.contrib import admin
from .models import (
    Customer, WarrantyRegistration, ClaimWarranty, Customer_Address,
    Cart, CartItem, Order, OTPRecord
)
from django.contrib.auth.models import Group

# Unregister the default Group model
admin.site.unregister(Group)

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'total_price', 'status')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_email', 'total_amount', 'status', 'ordered_date')
    list_filter = ('status', 'ordered_date')
    search_fields = ('id', 'customer__user__username', 'customer__user__email')
    readonly_fields = ('id', 'ordered_date', 'delivered_date')

    def customer_name(self, obj):
        return obj.customer.user.get_full_name() if obj.customer.user else "Unknown Customer"
    customer_name.short_description = 'Customer Name'

    def customer_email(self, obj):
        return obj.customer.user.email if obj.customer.user else "No Email"
    customer_email.short_description = 'Customer Email'

    def total_amount(self, obj):
        return obj.amount
    total_amount.short_description = 'Total Amount'

    def cart_items(self, obj):
        if obj.cart:
            return ", ".join([item.product.name for item in obj.cart.items.all()])
        return "No Cart Items"
    cart_items.short_description = 'Cart Items'

    def cart_quantities(self, obj):
        if obj.cart:
            return ", ".join([str(item.quantity) for item in obj.cart.items.all()])
        return "No Quantities"
    cart_quantities.short_description = 'Quantities'

    def cart_total_price(self, obj):
        if obj.cart:
            return sum(item.total_price for item in obj.cart.items.all())
        return 0
    cart_total_price.short_description = 'Cart Total Price'

    # Add these methods to the list_display
    list_display += ('cart_items', 'cart_quantities', 'cart_total_price')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer__user', 'cart')

# Register models
admin.site.register(Customer)
admin.site.register(WarrantyRegistration)
admin.site.register(ClaimWarranty)
admin.site.register(Customer_Address)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(OTPRecord)