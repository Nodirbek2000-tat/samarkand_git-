from django.db import models
from rest_framework import serializers

from .models import EditorUpload, Page, SiteSettings


class RelativeFileMixin:
    """Return `/media/...` instead of an absolute URL so files resolve through the frontend proxy."""

    def to_representation(self, value):
        if not value:
            return None
        try:
            return value.url
        except ValueError:
            return None


class RelativeImageField(RelativeFileMixin, serializers.ImageField):
    pass


class RelativeFileField(RelativeFileMixin, serializers.FileField):
    pass


class BaseModelSerializer(serializers.ModelSerializer):
    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        models.ImageField: RelativeImageField,
        models.FileField: RelativeFileField,
    }

    def to_internal_value(self, data):
        # Admin forms send a file only when it changes: "" / missing = keep, "null" = remove.
        if hasattr(data, "copy"):
            data = data.copy()
        cleared = []
        for name, field in self.fields.items():
            if not isinstance(field, serializers.FileField) or field.read_only or name not in data:
                continue
            value = data.get(name)
            if value in ("", "undefined", "null", None):
                data.pop(name)
                if value in ("null", None):
                    cleared.append(field.source)
        validated = super().to_internal_value(data)
        for source in cleared:
            validated[source] = ""  # empty FieldFile; columns are NOT NULL
        return validated


class SiteSettingsSerializer(BaseModelSerializer):
    class Meta:
        model = SiteSettings
        exclude = ["id", "created_at"]


class BlocksField(serializers.JSONField):
    """[{group, title, body}] — accepts a JSON string from multipart admin forms."""

    def to_internal_value(self, data):
        import json

        if isinstance(data, str):
            try:
                data = json.loads(data or "[]")
            except ValueError:
                raise serializers.ValidationError("Bloklar noto‘g‘ri formatda.")
        if not isinstance(data, list):
            raise serializers.ValidationError("Ro‘yxat kutilmoqda.")
        clean = []
        for item in data[:60]:
            if isinstance(item, dict) and (item.get("title") or item.get("body")):
                clean.append(
                    {
                        "group": str(item.get("group", "")).strip()[:40],
                        "title": str(item.get("title", "")).strip()[:300],
                        "body": str(item.get("body", "")).strip()[:3000],
                    }
                )
        return clean


class PageSerializer(BaseModelSerializer):
    section_label = serializers.CharField(source="get_section_display", read_only=True)
    blocks = BlocksField(required=False)

    class Meta:
        model = Page
        fields = [
            "id", "key", "section", "section_label", "title", "subtitle", "body", "blocks", "cover",
            "seo_description", "is_published", "published_at", "updated_at",
        ]
        read_only_fields = ["published_at", "updated_at"]


class EditorUploadSerializer(BaseModelSerializer):
    class Meta:
        model = EditorUpload
        fields = ["id", "file"]
