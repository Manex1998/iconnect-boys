from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg


# ==========================
# CATEGORY
# ==========================

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    # ✅ Support for nested categories
    parent = models.ForeignKey(
        "self", related_name="subcategories",
        on_delete=models.CASCADE, blank=True, null=True
    )

    # ✅ SEO + media
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)

    # ✅ General
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]   # keeps list alphabetical
        indexes = [models.Index(fields=["slug"])]  # faster lookups

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            # ✅ ensure slug uniqueness
            while Category.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{get_random_string(4)}"
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def full_name(self):
        """Show nested hierarchy e.g. 'Phones > iPhone > iPhone 14'"""
        names = [self.name]
        parent = self.parent
        while parent:
            names.append(parent.name)
            parent = parent.parent
        return " > ".join(reversed(names))
    
    def clean(self):
        # New: Prevent category from being its own parent
        if self.parent == self:
            raise ValidationError("A category cannot be its own parent.")
        super().clean()

    def get_all_subcategories(self):
        # New: Recursively fetch all subcategories
        subcategories = []
        for subcategory in self.subcategories.all():
            subcategories.append(subcategory)
            subcategories.extend(subcategory.get_all_subcategories())
        return subcategories




# ==========================
# BADGE (e.g. SALE, NEW)
# ==========================
class Badge(models.Model):
    BADGE_COLOR_CHOICES = [
        ('primary', 'Primary (Blue)'),
        ('success', 'Success (Green)'),
        ('warning', 'Warning (Yellow/Orange)'),
        ('danger', 'Danger (Red)'),
        ('info', 'Info (Light Blue)'),
    ]

    name = models.CharField(max_length=100, unique=True)
    color_class = models.CharField(max_length=20, choices=BADGE_COLOR_CHOICES, default='primary')
    text_color = models.CharField(max_length=20, blank=True, null=True,
                                  help_text="Optional custom text color (e.g., #FFFFFF)")
    bg_color = models.CharField(max_length=20, blank=True, null=True,
                                help_text="Optional custom background color (e.g., #2A59FE)")
    is_active = models.BooleanField(default=True)

     # New: Priority field for badge display order
    priority = models.PositiveIntegerField(default=0, help_text="Higher priority badges display first")

    class Meta:
        ordering = ["-priority", "name"]  # New: Order by priority

    def clean(self):
        # New: Ensure consistent color usage
        if self.color_class and (self.text_color or self.bg_color):
            raise ValidationError("Use either color_class or custom text_color/bg_color, not both.")
        super().clean()

    def __str__(self):
        return self.name


# ==========================
# PRODUCT
# ==========================

class Product(models.Model):
    CONDITION_CHOICES = [
        ("brand_new", "Brand New"),
        ("excellent", "Excellent"),
        ("like_new", "Like New"),
        ("good", "Good"),
        ("fair", "Fair"),
    ]

    STOCK_CHOICES = [
        ("in_stock", "In Stock"),
        ("low_stock", "Low Stock"),
        ("out_of_stock", "Out of Stock"),
    ]

    # Basic info
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.TextField(blank=True, null=True)
    full_description = models.TextField(blank=True, null=True)
    specifications = models.JSONField(blank=True, null=True)
    key_features = models.JSONField(blank=True, null=True)
    category = models.ForeignKey("Category", related_name="products", on_delete=models.CASCADE)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default="brand_new")
    badges = models.ManyToManyField("Badge", blank=True)

    # Stock & pricing
    stock_status = models.CharField(max_length=20, choices=STOCK_CHOICES, default="in_stock")
    stock_quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                    validators=[MinValueValidator(0)])
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)

    # Media
    image = models.ImageField(upload_to="products/")
    # We’ll use ProductImage model instead of additional_images M2M
    # default_image() property will fetch it

    # Ratings
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0,
                                 validators=[MinValueValidator(0), MaxValueValidator(5)])
    rating_count = models.PositiveIntegerField(default=0)

    # Meta fields
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # SEO
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    # New: Canonical URL for SEO
    canonical_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_featured"]),  # New: Index for is_featured
        ]

    def save(self, *args, **kwargs):
        # Slug generation
        if not self.slug:
            base_slug = slugify(self.title)
            unique_slug = base_slug
            while Product.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{get_random_string(4)}"
            self.slug = unique_slug

            # New: Auto-generate meta_title if not provided
        if not self.meta_title:
            self.meta_title = self.title
        super().save(*args, **kwargs)

        # SKU generation
        if not self.sku:
            category_prefix = self.category.name[:3].upper() if self.category else "PRO"
            self.sku = f"{category_prefix}-{Product.objects.count() + 1000}"

        super().save(*args, **kwargs)

    # --- Helpers ---
    @property
    def discount_percentage(self):
        if self.old_price and self.old_price > self.price:
            return round((self.old_price - self.price) / self.old_price * 100)
        return 0

    @property
    def discount_amount(self):
        if self.old_price and self.old_price > self.price:
            return self.old_price - self.price
        return 0

    @property
    def is_in_stock(self):
        return self.stock_status == "in_stock" and self.stock_quantity > 0

    @property
    def is_on_sale(self):
        return self.old_price is not None and self.old_price > self.price
    
    def is_new(self):
        # Updated: Use configurable threshold
        NEW_PRODUCT_DAYS = getattr(settings, "NEW_PRODUCT_DAYS", 7)
        return self.created_at >= timezone.now() - timedelta(days=NEW_PRODUCT_DAYS)

    @property
    def default_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    def update_average_rating(self):
        avg = self.reviews.aggregate(Avg("rating"))["rating__avg"]
        self.rating = avg if avg is not None else 0.0
        self.rating_count = self.reviews.count()
        self.save()

    def is_new(self):
        return self.created_at >= timezone.now() - timedelta(days=7)

    def __str__(self):
        return self.title


# ==========================
# PRODUCT VARIANT
# ==========================
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)  # e.g. "128GB - Black"
    color = models.CharField(max_length=50, blank=True, null=True)
    storage = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("product", "color", "storage")

    def __str__(self):
        return f"{self.product.title} - {self.name or f'{self.storage} {self.color}'}"

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def discount_percentage(self):
        if self.old_price and self.old_price > self.price:
            return round((self.old_price - self.price) / self.old_price * 100)
        return 0



# ==========================
# PRODUCT IMAGE
# ==========================
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "is_primary"],
                condition=models.Q(is_primary=True),
                name="unique_primary_image_per_product",
            )
        ]

    def __str__(self):
        return f"Image for {self.product.title}"



# ==========================
# PRODUCT REVIEW
# ==========================
class Rating(models.Model):
    product = models.ForeignKey(Product, related_name="ratings", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "user")

    def __str__(self):
        return f"{self.user.username} rated {self.product.title} {self.rating}/5"


# ==========================
# WISHLIST (Optional)
# ==========================
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username}'s wishlist - {self.product.title}"
