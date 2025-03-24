from django.urls import path
from .import views
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns = [

    path('',views.home,name='home'),
    path('auth/initiate/', views.AuthInitiateView.as_view(), name='auth-initiate'),
    path('auth/otp-login/', views.OTPLoginAPIView.as_view(), name='otp-login'),
    path('auth/otp-verify/', views.OTPVerifyAPIView.as_view(), name='otp-verify'),
    path('auth/verify-otp/', views.OTPVerificationView.as_view(), name='verify-otp'),
    path('auth/resend-otp/', views.ResendOTPView.as_view(), name='resend-otp'),
    path('auth/verify-otp2/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/complete-registration/', views.CompleteRegistrationView.as_view(), name='complete-registration'),
    path('alerts/enable/',views.EnableAlertView.as_view(),name='enable_alert_view'),
    path('alerts/verify/',views.VerifyAlertView.as_view(),name='verify_alert_view'),
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('token/refresh/',TokenRefreshView.as_view(), name='token_refresh'),


    path('register-warranty/', views.WarrantyRegistrationAPIView.as_view(), name='register-warranty'),
    path('confirm-payment-warranty/', views.confirm_payment_warranty, name='confirm_payment_warranty'),
    path('validate-warranty/', views.validate_warranty_number, name='validate_warranty_number'),
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

    # Payment

    # Create PaymentIntent
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),

    # Confirm Payment
    path('confirm-payment/', views.confirm_payment, name='confirm_payment'),



    # Test

    path("process-text/", views.process_text, name="process_text"),
    #
    # path('process-image/', views.process_image, name='process_image'),

    # Database Backup
    #path('backup/', views.backup_database, name='backup_database'),

    # Order Details
    path('orders/<int:customer_id>/', views.CustomerOrderDetailView.as_view(), name='customer-order-detail'),

    #Order Detail view

    path('orders_detail/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),

    # Send RFQ
    path("send-rfq/", views.RFQRequestView.as_view(), name="send_rfq"),

    # UUID

    path('generate-uuid/',views.GenerateAnonymousUUID.as_view(),name='generate-uuid'),

    # SAVE DESIGN

    path('save-design/', views.CustomerDesignView.as_view(), name='save_design'),

    # GET DESIGNS
    path('generate-image/<uuid:uid>/', views.generate_design_image, name='generate_design_image'),

    # send otp
    path('send-otp/', views.send_otp, name='send_otp'),

    path('verify-otp2/', views.verify_otp2, name='verify_otp'),

    path('reset-password/', views.reset_password, name='reset_password'),

    # Image store
    # path('image/upload/', views.upload_image, name='upload_image'),
    # path('check-wovlene/', views.check_wovlene, name='check_wovlene'),


]