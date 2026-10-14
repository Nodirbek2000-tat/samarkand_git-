from rest_framework import serializers

from apps.core.serializers import BaseModelSerializer

from .models import Announcement, Film, Gallery, GalleryImage, News, NewsImage


class NewsImageSerializer(BaseModelSerializer):
    class Meta:
        model = NewsImage
        fields = ["id", "news", "image", "caption", "order"]
        extra_kwargs = {"news": {"write_only": True}}


class NewsListSerializer(BaseModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    images_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = News
        fields = [
            "id", "slug", "title", "category", "category_label", "excerpt", "cover", "is_featured",
            "is_published", "published_at", "views", "images_count", "updated_at",
        ]


class NewsSerializer(NewsListSerializer):
    images = NewsImageSerializer(many=True, read_only=True)

    class Meta(NewsListSerializer.Meta):
        fields = NewsListSerializer.Meta.fields + ["body", "source_url", "images", "created_at"]
        read_only_fields = ["slug", "views", "created_at", "updated_at"]
        extra_kwargs = {"published_at": {"required": False}}


class FilmSerializer(BaseModelSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        url = attrs.get("video_url", getattr(self.instance, "video_url", ""))
        file = attrs.get("video_file", getattr(self.instance, "video_file", None))
        if not url and not file:
            raise serializers.ValidationError({"video_url": "YouTube havolasini kiriting yoki video fayl yuklang."})
        return attrs

    class Meta:
        model = Film
        fields = [
            "id", "slug", "title", "company", "owner_name", "description", "video_url", "video_file", "cover", "duration",
            "order", "is_published", "published_at", "created_at", "updated_at",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]


class GalleryImageSerializer(BaseModelSerializer):
    class Meta:
        model = GalleryImage
        fields = ["id", "gallery", "image", "caption", "order"]
        extra_kwargs = {"gallery": {"write_only": True}}


class GalleryListSerializer(BaseModelSerializer):
    images_count = serializers.IntegerField(read_only=True)
    preview = serializers.SerializerMethodField()

    class Meta:
        model = Gallery
        fields = [
            "id", "slug", "title", "description", "event_date", "location", "cover", "images_count", "preview",
            "is_published", "published_at", "updated_at",
        ]

    def get_preview(self, obj):
        images = getattr(obj, "preview_images", None)
        if images is None:
            images = list(obj.images.all()[:4])
        return [img.image.url for img in images[:4] if img.image]


class GallerySerializer(GalleryListSerializer):
    images = GalleryImageSerializer(many=True, read_only=True)

    class Meta(GalleryListSerializer.Meta):
        fields = GalleryListSerializer.Meta.fields + ["images", "created_at"]
        read_only_fields = ["slug", "created_at", "updated_at"]


class AnnouncementSerializer(BaseModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    gallery_slug = serializers.CharField(source="gallery.slug", read_only=True, default=None)
    is_upcoming = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            "id", "slug", "title", "kind", "kind_label", "excerpt", "body", "cover", "event_date", "ends_at",
            "location", "participants", "registration_url", "is_featured", "gallery", "gallery_slug", "is_upcoming",
            "is_published", "published_at", "created_at", "updated_at",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]

    def get_is_upcoming(self, obj):
        from django.utils import timezone

        end = obj.ends_at or obj.event_date
        return bool(end and end >= timezone.now())
