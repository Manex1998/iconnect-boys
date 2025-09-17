# Register your models here.
from django.contrib import admin
from .models import Category, Badge, Product, ProductVariant, ProductImage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ["name", "color_class", "priority", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "price", "stock_status", "is_active", "is_featured"]
    list_filter = ["category", "stock_status", "is_active", "is_featured"]
    search_fields = ["title", "sku"]
    prepopulated_fields = {"slug": ("title",)}

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["product", "name", "price", "stock"]
    #list_filter = ["is_default"]
    search_fields = ["name", "sku"]

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ["product", "is_primary", "order"]
    list_filter = ["is_primary"]
    search_fields = ["alt_text", "caption"]