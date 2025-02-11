from django.urls import path
from .import views

urlpatterns = [
    path('',views.dashboard,name='dash'),
    path('category/', views.category, name="category"),
    path('add-category/', views.add_category, name="add_category"),
    path('update_category/', views.update_category, name='update_category'),
    path('delete_category/<int:category_id>/', views.delete_category, name='delete_category'),

    # API CATEGORY
    path("categories/", views.list_categories, name="list_categories"),
    path("subcategories/<int:category_id>/", views.list_subcategories, name="list_subcategories"),

    # Product LIST
    path("products/", views.list_products, name="list_products"),

    # Product list based on category id
    path("products/category/<int:category_id>/", views.filter_products_by_category, name="filter_products_by_category"),

    # Product list based on subcategory_id
    path("products/subcategory/<int:subcategory_id>/", views.filter_products_by_subcategory,
         name="filter_products_by_subcategory"),

    #  Product Detail View
    path("product/<int:product_id>/", views.get_product_details, name="get_product_details"),
]