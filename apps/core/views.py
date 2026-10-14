from drf_spectacular.utils import extend_schema
from rest_framework import generics, parsers, viewsets
from rest_framework.permissions import AllowAny

from .api import PublishedQuerysetMixin, PublishToggleMixin
from .models import EditorUpload, Page, SiteSettings
from .permissions import IsStaff, IsSuperuser, is_admin
from .serializers import EditorUploadSerializer, PageSerializer, SiteSettingsSerializer

MULTIPART = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]


class SiteSettingsView(generics.RetrieveUpdateAPIView):
    """GET for everyone, PATCH for administrators (not editors)."""

    serializer_class = SiteSettingsSerializer
    parser_classes = MULTIPART

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsSuperuser()]

    def get_object(self):
        return SiteSettings.load()


class PageViewSet(PublishedQuerysetMixin, PublishToggleMixin, viewsets.ModelViewSet):
    """Editable content pages, addressed by their fixed `key`."""

    queryset = Page.objects.all()
    serializer_class = PageSerializer
    parser_classes = MULTIPART
    lookup_field = "key"
    filterset_fields = ["section", "is_published"]
    search_fields = ["title", "subtitle", "body"]
    ordering_fields = ["title", "updated_at", "section"]
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        return qs if is_admin(self.request.user) else qs.defer("seo_description")


class EditorUploadView(generics.CreateAPIView):
    queryset = EditorUpload.objects.all()
    serializer_class = EditorUploadSerializer
    permission_classes = [IsStaff]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @extend_schema(request={"multipart/form-data": EditorUploadSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
