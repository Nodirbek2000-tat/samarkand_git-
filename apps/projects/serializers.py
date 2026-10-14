import json

from rest_framework import serializers

from apps.core.serializers import BaseModelSerializer

from .models import Project, ProjectDocument, ProjectImage, ProjectParticipant


class ProjectImageSerializer(BaseModelSerializer):
    class Meta:
        model = ProjectImage
        fields = ["id", "project", "image", "caption", "order"]
        extra_kwargs = {"project": {"write_only": True}}


class ProjectDocumentSerializer(BaseModelSerializer):
    size = serializers.SerializerMethodField()
    extension = serializers.SerializerMethodField()

    class Meta:
        model = ProjectDocument
        fields = ["id", "project", "title", "file", "size", "extension", "order"]
        extra_kwargs = {"project": {"write_only": True}}

    def get_size(self, obj):
        try:
            return obj.file.size
        except (OSError, ValueError):
            return None

    def get_extension(self, obj):
        return obj.file.name.rsplit(".", 1)[-1].lower() if obj.file else None


class ProjectParticipantSerializer(BaseModelSerializer):
    class Meta:
        model = ProjectParticipant
        fields = ["id", "project", "company", "person", "role", "contribution", "order"]


class StatsField(serializers.JSONField):
    """List of {"value", "label"} pairs; accepts a JSON string too (multipart admin forms)."""

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data or "[]")
            except ValueError:
                raise serializers.ValidationError("Raqamlar noto‘g‘ri formatda.")
        if not isinstance(data, list):
            raise serializers.ValidationError("Ro‘yxat kutilmoqda.")
        clean = []
        for item in data[:12]:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Har bir element {value, label} bo‘lishi kerak.")
            value, label = str(item.get("value", "")).strip()[:40], str(item.get("label", "")).strip()[:120]
            if value or label:
                clean.append({"value": value, "label": label})
        return clean


class ProjectListSerializer(BaseModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id", "slug", "title", "category", "category_label", "status", "status_label", "summary", "metrics",
            "stats", "cover", "is_featured", "order", "is_published", "published_at", "updated_at",
        ]


class ProjectSerializer(ProjectListSerializer):
    images = ProjectImageSerializer(many=True, read_only=True)
    documents = ProjectDocumentSerializer(many=True, read_only=True)
    participants = ProjectParticipantSerializer(many=True, read_only=True)
    stats = StatsField(required=False)

    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + [
            "body", "objectives", "expected_results", "video_url", "website_url", "telegram_url", "instagram_url",
            "started_on", "finished_on", "budget", "images", "documents", "participants", "created_at",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]
