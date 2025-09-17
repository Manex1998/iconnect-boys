from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from .models import Cart, CartItem, Order, OrderItem
from product.models import Product, ProductVariant
from django.conf import settings
from .utils import generate_order_number
import json
from datetime import datetime, timedelta



@login_required
def cart_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    
    # Calculate subtotal and discount
    subtotal = sum(
        item.quantity * (item.product.price if not item.product.is_discounted else item.product.discount_price)
        for item in cart.items.select_related('product')
    )
    cart_discount = sum(
        item.quantity * (item.product.price - item.product.discount_price)
        for item in cart.items.select_related('product') if item.product.is_discounted
    )
    
    # Recently viewed items (session-based)
    recently_viewed_ids = request.session.get('recently_viewed', [])
    recently_viewed = Product.objects.filter(id__in=recently_viewed_ids, is_active=True)[:4]
    
    context = {
        'cart': cart,
        'cart_subtotal': subtotal,
        'cart_discount': cart_discount,
        'delivery_date': datetime.now() + timedelta(days=5),  # Example delivery date
        'recently_viewed': recently_viewed,
    }
    return render(request, 'cart.html', context)

@login_required
def update_cart_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        if quantity < 1:
            quantity = 1
        if quantity > 1:  # Example limit
            return JsonResponse({'success': False, 'message': 'Maximum quantity is 1 per item', 'quantity': cart_item.quantity}, status=400)
        
        cart_item.quantity = quantity
        cart_item.save()
        
        cart = cart_item.cart
        subtotal = sum(
            item.quantity * (item.product.price if not item.product.is_discounted else item.product.discount_price)
            for item in cart.items.select_related('product')
        )
        discount = sum(
            item.quantity * (item.product.price - item.product.discount_price)
            for item in cart.items.select_related('product') if item.product.is_discounted
        )
        
        return JsonResponse({
            'success': True,
            'subtotal': float(subtotal),
            'discount': float(discount),
            'total': float(cart.total),
            'quantity': cart.total_quantity
        })
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
def remove_cart_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        
        cart = Cart.objects.get(user=request.user)
        subtotal = sum(
            item.quantity * (item.product.price if not item.product.is_discounted else item.product.discount_price)
            for item in cart.items.select_related('product')
        )
        discount = sum(
            item.quantity * (item.product.price - item.product.discount_price)
            for item in cart.items.select_related('product') if item.product.is_discounted
        )
        
        return JsonResponse({
            'success': True,
            'subtotal': float(subtotal),
            'discount': float(discount),
            'total': float(cart.total),
            'quantity': cart.total_quantity
        })
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        return redirect('cart')
    
    # Placeholder for checkout logic
    context = {'cart': cart}
    return render(request, 'checkout.html', context)

def guest_checkout(request):
    # Placeholder for guest checkout
    return render(request, 'guest_checkout.html', {'message': 'Guest checkout not fully implemented'})

@login_required
def apply_promo_code(request):
    if request.method == 'POST':
        promo_code = request.POST.get('promo_code')
        # Implement promo code logic (e.g., validate and apply discount)
        return JsonResponse({'success': True, 'message': f'Promo code {promo_code} applied (placeholder)'})
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)



@login_required
def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id)
        if not product.is_in_stock:
            return JsonResponse({'success': False, 'message': 'Product is out of stock'}, status=400)

        # Get or create cart
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Get price (use variant if provided)
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
            price = variant.price
            discount_price = variant.discount_price if variant.is_on_sale else None
        else:
            variant = None
            price = product.price
            discount_price = product.discount_price if product.is_on_sale else None

        # Add or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return JsonResponse({
            'success': True,
            'message': f'{product.title} added to cart',
            'cart_total': float(cart.total),
            'cart_quantity': cart.total_quantity
        })
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)



@login_required
def create_order(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        return JsonResponse({'success': False, 'message': 'Cart is empty'}, status=400)

    order = Order.objects.create(
        user=request.user,
        order_number=generate_order_number(),
        status='PENDING',
        total_price=cart.total,
        shipping_cost=0.00,  # Add logic for shipping cost
        billing_name=request.user.get_full_name(),
        billing_email=request.user.email,
        billing_phone=request.user.phone_number or '',
    )

    for item in cart.items.all():
        price = item.product.discount_price if item.product.is_discounted else item.product.price
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price_at_order=price,
            discount_price_at_order=item.product.discount_price if item.product.is_discounted else None
        )

    # Clear cart
    cart.items.all().delete()
    return JsonResponse({'success': True, 'message': 'Order created', 'order_id': order.id})


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    context = {'cart': cart}
    return render(request, 'checkout.html', context)