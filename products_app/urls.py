from django.urls import path
from .import views

urlpatterns = [
    path('',views.dashboard,name='dash'),
    path('category/', views.category, name="category"),
    path('add-category/', views.add_category, name="add_category"),
    path('update_category/', views.update_category, name='update_category'),
    path('delete_category/<int:category_id>/', views.delete_category, name='delete_category'),

    #  Product Detail View
    path("product/<int:product_id>/", views.get_product_details, name="get_product_details"),

    # Parent Category

    path('parent-categories/', views.ParentCategoryListView.as_view(), name='parent-categories-list'),

    # Category by parent category id

    path('parent-category/<int:parent_category_id>/categories/', views.CategoryByParentView.as_view(),
         name='category-by-parent'),

    # SubCategory list using parent id an category id

    path('subcategories/', views.SubcategoryListView.as_view(), name='subcategory-list'),

    # Product LIST
    path("products/", views.list_products, name="list_products"),

    # Product List based on Parent Category ID
    path('products_cat/', views.ProductListByParentCategory.as_view(), name='product-list-by-parent-category'),

    # Product list based on category id

    path('products-by-category/', views.ProductListByCategory.as_view(), name='product-list-by-category'),

    # Product list based on sub category id

    path('products-by-subcategory/', views.ProductListBySubcategory.as_view(), name='product-list-by-subcategory'),

    # Category and Sub category list based on parent category id

    path('categories/<int:parent_category_id>/', views.get_categories_by_parent, name='get_categories_by_parent'),

    # Search

    path("search/", views.search_products, name="search_products"),





]
