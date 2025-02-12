from django.urls import path
from .import views
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns = [

    path('',views.home,name='home'),
    path('register/', views.CustomerRegistrationView.as_view(), name='customer-registration'),
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('token/refresh/',TokenRefreshView.as_view(), name='token_refresh'),
    path("custom-product/create/", views.create_custom_product, name="create_custom_product"),
    path("cart/add-custom-product/", views.add_custom_product_to_cart, name="add_custom_product_to_cart"),
    path("cart/details/", views.get_cart_details, name="get_cart_details"),
    path('logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('create-order/', views.CreateOrderView.as_view(), name='create_order'),
    path('order/<int:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('order/<int:order_id>/update/', views.OrderUpdateView.as_view(), name='order_update'),
    path('cartitem/<int:cartitem_id>/', views.CartItemDetailView.as_view(), name='cartitem_detail'),
    path('cartitem/<int:cartitem_id>/edit/', views.CartItemEditView.as_view(), name='cartitem_edit'),
    path('cartitem/<int:cartitem_id>/delete/', views.CartItemDeleteView.as_view(), name='cartitem_delete'),
    path('register-warranty/', views.WarrantyRegistrationAPIView.as_view(), name='register-warranty'),
    path("create_claim_warranty/", views.create_claim_warranty, name="create_claim_warranty"),
    path('custom-products/', views.list_custom_products, name='list_custom_products'),
    path('custom-product/edit/<int:product_id>/', views.edit_custom_product, name='edit_custom_product'),
    path('customer-address/create/', views.create_customer_address, name='create_customer_address'),
    path('customer-addresses/<int:customer_id>/', views.get_customer_addresses, name='get_customer_addresses'),
    path('edit-customer-address/<int:address_id>/', views.edit_customer_address, name='edit_customer_address'),

]