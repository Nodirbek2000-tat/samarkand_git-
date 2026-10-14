from rest_framework import viewsets

from apps.core.api import MULTIPART, PublishedQuerysetMixin, ReorderMixin

from .models import Partner
from .serializers import PartnerSerializer


class PartnerViewSet(PublishedQuerysetMixin, ReorderMixin, viewsets.ModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    parser_classes = MULTIPART
    filterset_fields = ["kind", "is_published"]
    search_fields = ["name", "country", "description"]
    ordering_fields = ["order", "name"]
    pagination_class = None
