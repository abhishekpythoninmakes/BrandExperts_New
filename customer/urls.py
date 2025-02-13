from django.urls import path
from .import views
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns = [

    path('',views.home,name='home'),
    path('register/', views.CustomerRegistrationView.as_view(), name='customer-registration'),
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('token/refresh/',TokenRefreshView.as_view(), name='token_refresh'),


    path('register-warranty/', views.WarrantyRegistrationAPIView.as_view(), name='register-warranty'),
    path("create_claim_warranty/", views.create_claim_warranty, name="create_claim_warranty"),
    path('create-customer-address/', views.create_customer_address, name='create_customer_address'),
    path('customer-addresses/<int:customer_id>/', views.get_customer_addresses, name='get_customer_addresses'),
    path('edit-customer-address/<int:address_id>/', views.edit_customer_address, name='edit_customer_address'),

    # Create Cart
    path('cart/',views.create_or_update_cart, name='create_or_update_cart'),

    # Update CartItem
    path("cartitem/update/<int:cart_item_id>/", views.UpdateCartItemView.as_view(), name="update_cart_item"),

    # CartITEM Delete

    path("cartitem/delete/<int:cart_item_id>/", views.DeleteCartItemView.as_view(), name="delete_cart_item"),

    # Order

    path('create-order/', views.create_order, name='create-order'),

]