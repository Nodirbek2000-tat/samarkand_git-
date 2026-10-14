from rest_framework import serializers

from apps.core.permissions import is_admin
from apps.core.serializers import BaseModelSerializer

from .models import BoardMember, CouncilMember, Leader, Meeting, Recognition

PERSON_BASE = ["id", "slug", "full_name", "photo", "bio", "is_active", "order", "updated_at"]


class CouncilMemberSerializer(BaseModelSerializer):
    class Meta:
        model = CouncilMember
        fields = PERSON_BASE + [
            "company", "position", "industry", "website", "contact_email", "contact_phone", "show_contacts", "joined_year",
        ]
        read_only_fields = ["slug", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if not (request and is_admin(request.user)) and not instance.show_contacts:
            data["contact_email"] = ""
            data["contact_phone"] = ""
        return data


class BoardMemberSerializer(BaseModelSerializer):
    role_label = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = BoardMember
        fields = PERSON_BASE + ["role", "role_label", "workplace"]
        read_only_fields = ["slug", "updated_at"]


class LeaderSerializer(BaseModelSerializer):
    class Meta:
        model = Leader
        fields = PERSON_BASE + ["position", "organization", "phone", "email", "reception_hours"]
        read_only_fields = ["slug", "updated_at"]


class MeetingSerializer(BaseModelSerializer):
    gallery_slug = serializers.CharField(source="gallery.slug", read_only=True, default=None)

    class Meta:
        model = Meeting
        fields = [
            "id", "slug", "title", "date", "host_company", "location", "agenda", "outcome", "gallery", "gallery_slug",
            "is_published", "published_at", "updated_at",
        ]
        read_only_fields = ["slug", "updated_at"]


class RecognitionSerializer(BaseModelSerializer):
    class Meta:
        model = Recognition
        fields = ["id", "full_name", "company", "award", "year", "photo", "description", "is_published", "order", "updated_at"]
        read_only_fields = ["updated_at"]
