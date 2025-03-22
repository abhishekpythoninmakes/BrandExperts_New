from django.urls import path
from .import views


urlpatterns = [
    path('users/',views.users_list,name='users_list'),
    path('placeholders/json/', views.placeholder_json, name='placeholder_json'),
    path('placeholders/create/', views.create_placeholder, name='create_placeholder'),

    path('track-email/<uuid:tracking_id>/', views.track_email_open, name='track_email_open'),


]