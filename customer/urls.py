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
    path('api/order/<int:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('api/order/<int:order_id>/update/', views.OrderUpdateView.as_view(), name='order_update'),

]