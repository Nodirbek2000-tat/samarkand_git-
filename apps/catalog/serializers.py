from rest_framework import serializers

from apps.core.serializers import BaseModelSerializer

from .models import Category, Company, CompanyImage, Product, ProductImage


class CategorySerializer(BaseModelSerializer):
    companies_count = serializers.IntegerField(read_only=True)
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "slug", "title", "image", "order", "companies_count", "products_count"]


class CategoryRefSerializer(BaseModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "slug", "title"]


class ImageSerializer(BaseModelSerializer):
    class Meta:
        model = CompanyImage
        fields = ["id", "image"]


class ProductImageSerializer(BaseModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


class CompanyRefSerializer(BaseModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "slug", "title", "logo"]


class ProductSerializer(BaseModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    company = CompanyRefSerializer(read_only=True)
    category = CategoryRefSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "images", "company", "category"]


class CompanyListSerializer(BaseModelSerializer):
    category = CategoryRefSerializer(read_only=True)
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Company
        fields = ["id", "slug", "title", "logo", "address", "category", "products_count"]


class CompanyProductSerializer(BaseModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "images"]


class CompanySerializer(CompanyListSerializer):
    images = ImageSerializer(many=True, read_only=True)
    products = serializers.SerializerMethodField()

    class Meta(CompanyListSerializer.Meta):
        fields = CompanyListSerializer.Meta.fields + [
            "description", "phone", "sales_manager", "email", "website", "telegram", "instagram", "facebook",
            "youtube", "whatsapp", "images", "products",
        ]

    def get_products(self, obj):
        products = [p for p in obj.products.all() if p.is_published]
        return CompanyProductSerializer(products, many=True, context=self.context).data
