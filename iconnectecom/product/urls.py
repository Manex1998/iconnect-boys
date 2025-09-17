from django.urls import path
from .views import product_list, product_detail, add_to_cart, toggle_wishlist, select_variant, submit_review, subscribe_newsletter

urlpatterns = [
    path('', product_list, name='product_list'),
    path('product/<slug:slug>/', product_detail, name='product_detail'),
    path('cart/add/', add_to_cart, name='add_to_cart'),
    path('wishlist/toggle/', toggle_wishlist, name='toggle_wishlist'),
    path('product/select-variant/', select_variant, name='select_variant'),
    path('product/<int:product_id>/review/', submit_review, name='submit_review'),
    path('newsletter/subscribe/', subscribe_newsletter, name='subscribe_newsletter'),
]