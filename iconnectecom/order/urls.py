from django.urls import path
from .views import  add_to_cart, cart_view, update_cart_item, remove_cart_item, checkout, guest_checkout, apply_promo_code

urlpatterns = [

    path('cart/add/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_view, name='cart'),
    path('cart/update/', update_cart_item, name='update_cart_item'),
    path('cart/remove/', remove_cart_item, name='remove_cart_item'),
    path('checkout/', checkout, name='checkout'),
    path('guest-checkout/', guest_checkout, name='guest_checkout'),
    path('cart/promo-code/', apply_promo_code, name='apply_promo_code'),

]