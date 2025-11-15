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


    # Product LIST
    path("products/", views.list_products, name="list_products"),

    # Product List based on Parent Category ID
    path('products_cat/', views.ProductListByParentCategory.as_view(), name='product-list-by-parent-category'),

    # Product list based on category id

    path('products-by-category/', views.ProductListByCategory.as_view(), name='product-list-by-category'),

    # Category and products list based on parent category id

    path('categories/<int:parent_category_id>/', views.get_categories_and_products_by_parent, name='get_categories_by_parent'),

    # Search

    path("search/", views.search_products, name="search_products"),

    #  Warranty plan based on price range

    path('get-warranty-by-price-range/<str:price_range>/', views.get_warranty_by_price_range,name='get_warranty_by_price_range'),


    # Wrranty plan price range
    path("price-ranges/", views.PriceRangeListAPIView.as_view(), name="price-ranges"),

    # Product Offer Slider
    path('offers/', views.offer_list, name='offer-list'),

    # Designer rate
    path('designer-rates/', views.DesignerRateAPIView.as_view(), name='designer-rates'),

    # Banner Image
    path('banners/', views.BannerImageListView.as_view(), name='banner-list'),

    # Testimonials

    path('testimonials/', views.get_all_testimonials, name='testimonials-list'),

    # Site visit amount

    path('site-visit/', views.get_site_visit_amount, name='site-visit-amount'),


    # Update
    path('update-product-dimensions/', views.UpdateProductDimensionsView.as_view(), name='update_product_dimensions'),

    # Product Price

    path('product-price/', views.ProductPriceView.as_view(), name='product-price'),

    # Produt Serializer for editor

    path('product-basic-details/', views.ProductBasicDetailView.as_view(), name='product-basic-detail-list'),

    # QUERY
    # path('square-signs-report/', views.export_square_signs_products, name='square_signs_report'),

    path('new/parent-categories/', views.parent_category_list_create, name='parent-category-list-create'),
    path('new/parent-categories/<int:pk>/', views.parent_category_detail, name='parent-category-detail'),

    # Category URLs
    path('categories/', views.category_list_create, name='category-list-create'),
    path('new/categories/<int:pk>/', views.category_detail, name='category-detail'),

    path('new/products/', views.product_list_create, name='product-list-create'),
    path('new/products/<int:pk>/', views.product_detail, name='product-detail'),

    path('new/products/filter/', views.product_filter_list, name='product-filter-list'),
    path('new/products/filter-options/', views.product_filter_options, name='product-filter-options'),

    # Inventory Management URLs
    path('inventory/stock/', views.inventory_stock_list, name='inventory-stock-list'),
    path('inventory/restore-stock/', views.restore_product_stock, name='restore-product-stock'),
    path('inventory/low-stock-alerts/', views.low_stock_alerts, name='low-stock-alerts'),
    path('inventory/dashboard/', views.inventory_dashboard, name='inventory-dashboard'),

]
