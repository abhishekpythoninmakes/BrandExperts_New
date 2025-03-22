from django.urls import path
from .import views


urlpatterns = [

    path('',views.home_partner,name='home_partner'),
    path('profile/',views.user_profile,name='user_profile'),
    path('partner-contacts/<int:user_id>/', views.PartnerContactsAPIView.as_view(), name='partner-contacts'),
    path('contacts/<int:pk>/', views.ContactDeleteAPIView.as_view(), name='delete-contact'),
    path('create_contacts/', views.ContactCreateAPIView.as_view(), name='create-contact'),

]