from django.urls import path
from .import views
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns = [

    path('',views.home,name='home'),
    path('register/', views.CustomerRegistrationView.as_view(), name='customer-registration'),
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('token/refresh/',TokenRefreshView.as_view(), name='token_refresh'),
    path("custom-product/create/", views.create_custom_product, name="create_custom_product"),
]