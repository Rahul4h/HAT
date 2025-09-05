
from django.urls import path
from app import views  # type: ignore
from django.contrib.auth.views import LogoutView

urlpatterns = [
   path('', views.index, name='index'),
   path ('about', views.about, name='about'),
   path ('contact', views.contact, name='contact'),
   path ('blog/', views.handleBlog, name='handleBlog'),
   path ('login', views.handlelogin, name='handlelogin'),
   path ('search', views.search, name='search'),
   path ('logout', views.handlelogout, name='handlelogout'),
   path ('signup', views.handlesignup, name='handlesignup'),
   #path('service',views.service, name='service'),
   path('product/<int:id>/', views.product_detail, name='product_detail'),
   path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
   path('cart/', views.cart_view, name='cart'),
   path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),
   path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
   path('checkout/<int:product_id>/', views.checkout, name='checkout'),
   path('initiate-payment/', views.initiate_sslcommerz_payment, name='initiate_payment'),
   path('payment-success/', views.your_success_view, name='payment_success'),
   path('payment-fail/', views.your_fail_view, name='payment_fail'),
   path('payment-cancel/', views.your_cancel_view, name='payment_cancel'),
   path('category/<str:category_name>/', views.category_products, name='category_products'),
   path('reorder/<int:product_id>/', views.reorder, name='reorder'),
   path('blog/<int:blog_id>/', views.blog_detail, name='blog_detail'),
   path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
   path('my-orders/', views.order_list, name='order_list'),
   path('update-order/<int:order_id>/', views.update_order, name='update_order'),
   path('deliveryboy/login/', views.deliveryboy_login, name='deliveryboy_login'),
   path('deliveryboy/home/', views.deliveryboy_home, name='deliveryboy_home'),
   path('deliveryboy/signup/', views.deliveryboy_signup, name='deliveryboy_signup'),
   path(
        'deliveryboy/logout/',
        views.deliveryboy_logout,
        name='deliveryboy_logout'
    ),

   path('delivery/assign/', views.assign_delivery_task, name='assign_delivery_task'),
   path('delivery/return/', views.assign_return_task,   name='assign_return_task'),
   #path('delivery/mark-delivered/<int:order_id>/', views.mark_order_delivered, name='mark_order_delivered'),
   #path('delivered/', views.delivered_orders_view, name='delivered_orders'),
   #path('my-orders/delivered/', views.delivered_orders_view, name='delivered_orders'),
   #path('request-return/<int:order_id>/', views.request_return, name='request_return'),
   path('return-request/<int:order_id>/', views.create_return_request, name='create_return_request'),
   path('return/mark-collected/<int:return_id>/', views.mark_return_collected, name='mark_return_collected'),
   path('activate/<uid>/<token>/', views.activate, name='activate'),
   path('confirm-delivery/<int:order_id>/', views.confirm_delivery, name='confirm_delivery'),
  # path('confirm-delivery/<int:order_id>/', views.confirm_delivery, name='confirm_delivery'),
   path('delivery/mark-delivered/<int:delivery_order_id>/', views.mark_order_delivered, name='mark_order_delivered'),
   path('checkout/success/', views.stripe_success, name='stripe_success'),
   path('checkout/cancel/', views.stripe_cancel, name='stripe_cancel'),
   path('order/update/success/', views.update_order_success, name='update_order_success'),
   path('order/update/cancel/', views.update_order_cancel, name='update_order_cancel'),
   





]



  






