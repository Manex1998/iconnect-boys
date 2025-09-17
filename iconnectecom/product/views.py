from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Product, ProductImage, ProductVariant, Category, Wishlist, Rating
from django.core.exceptions import ValidationError
import json

def product_list(request):
    # Get category if specified
    category_slug = request.GET.get('category')
    category = None
    if category_slug:
        category = Category.objects.filter(slug=category_slug).first()

    # Get products
    products = Product.objects.filter(is_active=True)
    if category:
        products = products.filter(category__in=category.get_all_subcategories() + [category])

    # Filter by condition
    condition = request.GET.get('condition')
    if condition:
        products = products.filter(condition=condition)

    # Sort
    sort = request.GET.get('sort', 'price')
    if sort == 'price':
        products = products.order_by('price')
    elif sort == '-price':
        products = products.order_by('-price')
    elif sort == '-created_at':
        products = products.order_by('-created_at')
    elif sort == '-rating':
        products = products.order_by('-rating')

    # Pagination
    paginator = Paginator(products, 6)  # 6 products per page
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    # Wishlist
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    context = {
        'products': products_page,
        'category': category,
        'condition_choices': Product.CONDITION_CHOICES,
        'sort_option': {
            'price': 'Price: Low to High',
            '-price': 'Price: High to Low',
            '-created_at': 'Newest First',
            '-rating': 'Best Rating'
        }.get(sort, 'Price: Low to High'),
        'wishlist_product_ids': wishlist_product_ids,
    }
    return render(request, 'product_list.html', context)

# AJAX view for adding to cart (placeholder)
def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        # Implement cart logic here
        return JsonResponse({'success': True, 'message': 'Added to cart'})
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# AJAX view for toggling wishlist
@login_required
def toggle_wishlist(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')
        product = Product.objects.get(id=product_id)
        if action == 'add':
            Wishlist.objects.get_or_create(user=request.user, product=product)
        else:
            Wishlist.objects.filter(user=request.user, product=product).delete()
        return JsonResponse({'success': True, 'message': f'Wishlist updated'})
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)




def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Get selected variant (default to the product's default variant or first variant)
    variant_id = request.session.get(f'selected_variant_{product.id}')
    selected_variant = None
    if variant_id:
        selected_variant = product.variants.filter(id=variant_id).first()
    if not selected_variant:
        selected_variant = product.variants.filter(is_default=True).first() or product.variants.first()

    # Wishlist
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    # Related products (e.g., same category, excluding current product)
    related_products = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'selected_variant': selected_variant,
        'condition_choices': Product.CONDITION_CHOICES,
        'wishlist_product_ids': wishlist_product_ids,
        'related_products': related_products,
        # Example specifications (replace with actual data or add to model)
        'product.specifications': {
            'Display': {
                'Size': '6.1 inches',
                'Technology': 'Super Retina XDR',
                'Resolution': '2532 x 1170 pixels',
                'Brightness': '625 nits (typical)',
                'Features': 'True Tone, Wide color, Haptic Touch',
            },
            'Chip': {
                'Name': 'A14 Bionic',
                'CPU': '6-core',
                'GPU': '4-core',
                'Neural Engine': '16-core',
            },
            'Camera': {
                'Dual 12MP system': 'Ultra Wide and Wide',
                'Optical zoom': '2x zoom out',
                'Digital zoom': 'Up to 5x',
                'Video recording': '4K at 24, 30, or 60 fps',
                'Front camera': '12MP TrueDepth',
            },
            'Power & Battery': {
                'Video playback': 'Up to 17 hours',
                'Fast charging': '50% in 30 minutes',
                'Wireless charging': 'MagSafe and Qi',
            },
        },
        'product.key_features': [
            '6.1-inch Super Retina XDR display',
            'A14 Bionic chip with next-generation Neural Engine',
            'Dual-camera system with 12MP Ultra Wide and Wide cameras',
            'Night mode, Deep Fusion, Smart HDR 3, and 4K Dolby Vision HDR recording',
            '5G connectivity for faster downloads and streaming',
            'Industry-leading IP68 water resistance',
            'Ceramic Shield front cover for 4x better drop performance',
        ],
    }
    return render(request, 'product_detail.html', context)

# AJAX view for selecting variant
def select_variant(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        variant = get_object_or_404(ProductVariant, id=variant_id)
        product = variant.product
        request.session[f'selected_variant_{product.id}'] = variant_id
        return JsonResponse({
            'success': True,
            'variant': {
                'price': str(variant.price),
                'old_price': str(variant.old_price) if variant.old_price else None,
                'discount_amount': str(variant.discount_amount) if variant.is_on_sale else None,
            }
        })
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# AJAX view for submitting review
@login_required
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        review_text = request.POST.get('review')
        try:
            rating_obj = Rating.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                review=review_text
            )
            product.update_average_rating()
            return redirect('product_detail', slug=product.slug)
        except ValidationError as e:
            return render(request, 'product_detail.html', {'product': product, 'error': str(e)})
    return redirect('product_detail', slug=product.slug)

# Placeholder for newsletter subscription
def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # Implement newsletter subscription logic here
        return JsonResponse({'success': True, 'message': 'Subscribed successfully'})
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
