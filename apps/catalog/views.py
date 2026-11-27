"""Read-only public API of the catalog; editing happens in the Django admin."""

from django.db.models import Count, F, Prefetch, Q, Value
from django.db.models.functions import Lower, Replace
from rest_framework import viewsets

from apps.core.api import IdOrSlugLookupMixin, PublishedQuerysetMixin

from .models import Category, Company, Product
from .serializers import CategorySerializer, CompanyListSerializer, CompanySerializer, ProductSerializer

PUBLISHED_PRODUCTS = Q(products__is_published=True)
# «ALFA» MChJ and "Alfa" sort as alfa — quotes and case do not decide the order
SORT_TITLE = Lower(Replace(Replace(Replace(F("title"), Value("«"), Value("")), Value("»"), Value("")), Value('"'), Value("")))


class CategoryViewSet(IdOrSlugLookupMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.order_by("order", "id").annotate(
            companies_count=Count("companies", filter=Q(companies__is_published=True), distinct=True),
            products_count=Count("products", filter=PUBLISHED_PRODUCTS, distinct=True),
        )


class CompanyViewSet(IdOrSlugLookupMixin, PublishedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Company.objects.select_related("category").annotate(
        products_count=Count("products", filter=PUBLISHED_PRODUCTS)
    ).order_by(SORT_TITLE, "id")
    filterset_fields = {"category__slug": ["exact"]}
    search_fields = ["title", "description", "address", "products__name"]
    ordering_fields = ["title", "products_count"]

    def get_serializer_class(self):
        return CompanySerializer if self.action == "retrieve" else CompanyListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "retrieve":
            qs = qs.prefetch_related("images", Prefetch("products", queryset=Product.objects.prefetch_related("images")))
        return qs.distinct() if self.request.query_params.get("search") else qs


class ProductViewSet(PublishedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(company__is_published=True).select_related("company", "category").prefetch_related("images").order_by("name", "id")
    serializer_class = ProductSerializer
    filterset_fields = {"category__slug": ["exact"], "company__slug": ["exact"]}
    search_fields = ["name", "description", "company__title"]
    ordering_fields = ["name"]
