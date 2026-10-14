from rest_framework import serializers

from apps.core.serializers import BaseModelSerializer

from .models import Partner


class PartnerSerializer(BaseModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = Partner
        fields = [
            "id", "name", "kind", "kind_label", "logo", "country", "website", "description", "is_published", "order",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]
