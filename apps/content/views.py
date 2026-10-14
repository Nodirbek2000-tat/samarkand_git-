from django.db.models import Count, F, Prefetch, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.api import (
    MULTIPART,
    IdOrSlugLookupMixin,
    PublishedQuerysetMixin,
    PublishToggleMixin,
    ReorderMixin,
    bulk_create_images,
)
from apps.core.permissions import IsStaff, is_admin

from .models import Announcement, Film, Gallery, GalleryImage, News, NewsImage
from .serializers import (
    AnnouncementSerializer,
    FilmSerializer,
    GalleryImageSerializer,
    GalleryListSerializer,
    GallerySerializer,
    NewsImageSerializer,
    NewsListSerializer,
    NewsSerializer,
)


class NewsViewSet(IdOrSlugLookupMixin, PublishedQuerysetMixin, PublishToggleMixin, viewsets.ModelViewSet):
    queryset = News.objects.annotate(images_count=Count("images")).order_by("-published_at", "-created_at")
    parser_classes = MULTIPART
    filterset_fields = ["category", "is_featured", "is_published"]
    search_fields = ["title", "excerpt", "body"]
    ordering_fields = ["published_at", "created_at", "title", "views"]
    ordering = ["-published_at", "-created_at"]

    def get_serializer_class(self):
        return NewsListSerializer if self.action == "list" else NewsSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action != "list":
            qs = qs.prefetch_related("images")
        return qs

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        if not is_admin(request.user) and request.query_params.get("track") == "1":
            News.objects.filter(pk=obj.pk).update(views=F("views") + 1)
        return Response(self.get_serializer(obj).data)

    @extend_schema(request={"multipart/form-data": {"type": "object", "properties": {"files": {"type": "array"}}}})
    @action(detail=True, methods=["post"], permission_classes=[IsStaff], url_path="images")
    def upload_images(self, request, *args, **kwargs):
        news = self.get_object()
        created = bulk_create_images(news, request.FILES.getlist("files"), NewsImage, "news")
        return Response(NewsImageSerializer(created, many=True).data, status=201)


class NewsImageViewSet(ReorderMixin, viewsets.ModelViewSet):
    queryset = NewsImage.objects.all()
    serializer_class = NewsImageSerializer
    permission_classes = [IsStaff]
    parser_classes = MULTIPART
    filterset_fields = ["news"]
    pagination_class = None


class FilmViewSet(IdOrSlugLookupMixin, PublishedQuerysetMixin, PublishToggleMixin, ReorderMixin, viewsets.ModelViewSet):
    queryset = Film.objects.all()
    serializer_class = FilmSerializer
    parser_classes = MULTIPART
    search_fields = ["title", "company", "owner_name", "description"]
    ordering_fields = ["order", "published_at", "title"]


class AnnouncementViewSet(IdOrSlugLookupMixin, PublishedQuerysetMixin, PublishToggleMixin, viewsets.ModelViewSet):
    queryset = Announcement.objects.select_related("gallery")
    serializer_class = AnnouncementSerializer
    parser_classes = MULTIPART
    filterset_fields = ["kind", "is_featured", "is_published"]
    search_fields = ["title", "excerpt", "body", "location"]
    ordering_fields = ["event_date", "published_at", "title"]

    def get_queryset(self):
        qs = super().get_queryset()
        when = self.request.query_params.get("when")
        now = timezone.now()
        upcoming = Q(ends_at__gte=now) | Q(ends_at__isnull=True, event_date__gte=now)
        if when == "upcoming":
            qs = qs.filter(upcoming).order_by("event_date")
        elif when == "past":
            qs = qs.exclude(upcoming).order_by("-event_date")
        return qs


class GalleryViewSet(IdOrSlugLookupMixin, PublishedQuerysetMixin, PublishToggleMixin, viewsets.ModelViewSet):
    parser_classes = MULTIPART
    search_fields = ["title", "description", "location"]
    ordering_fields = ["event_date", "created_at", "title"]

    def get_queryset(self):
        # explicit order: Meta.ordering is ignored once the query is aggregated
        qs = Gallery.objects.annotate(images_count=Count("images")).order_by("-event_date", "-created_at")
        if self.action == "list":
            qs = qs.prefetch_related(
                Prefetch("images", queryset=GalleryImage.objects.order_by("order", "id"), to_attr="preview_images")
            )
        else:
            qs = qs.prefetch_related("images")
        self.queryset = qs
        return super().get_queryset()

    def get_serializer_class(self):
        return GalleryListSerializer if self.action == "list" else GallerySerializer

    @extend_schema(request={"multipart/form-data": {"type": "object", "properties": {"files": {"type": "array"}}}})
    @action(detail=True, methods=["post"], permission_classes=[IsStaff], url_path="images")
    def upload_images(self, request, *args, **kwargs):
        gallery = self.get_object()
        created = bulk_create_images(gallery, request.FILES.getlist("files"), GalleryImage, "gallery")
        if not gallery.cover and created:
            gallery.cover = created[0].image.name
            gallery.save(update_fields=["cover", "updated_at"])
        return Response(GalleryImageSerializer(created, many=True).data, status=201)


class GalleryImageViewSet(ReorderMixin, viewsets.ModelViewSet):
    queryset = GalleryImage.objects.all()
    serializer_class = GalleryImageSerializer
    permission_classes = [IsStaff]
    parser_classes = MULTIPART
    filterset_fields = ["gallery"]
    pagination_class = None
