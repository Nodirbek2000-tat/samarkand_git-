from django.contrib import admin

from .models import Category, Company, CompanyImage, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "order"]
    list_editable = ["order"]


class CompanyImageInline(admin.TabularInline):
    model = CompanyImage
    extra = 0


class ProductInline(admin.TabularInline):
    model = Product
    fields = ["name", "category", "is_published"]
    extra = 0
    show_change_link = True


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "phone", "is_published"]
    list_filter = ["category", "is_published"]
    search_fields = ["title", "address", "description"]
    inlines = [CompanyImageInline, ProductInline]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "category", "is_published"]
    list_filter = ["category", "is_published"]
    search_fields = ["name", "company__title"]
    autocomplete_fields = ["company"]
    inlines = [ProductImageInline]
