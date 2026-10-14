from rest_framework import serializers

from apps.core.serializers import BaseModelSerializer

from .models import ForumEdition, Nomination, Winner


class WinnerSerializer(serializers.ModelSerializer):
    level_label = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = Winner
        fields = ["id", "level", "level_label", "name", "note", "order"]
        read_only_fields = ["order"]


class NominationSerializer(serializers.ModelSerializer):
    winners = WinnerSerializer(many=True, read_only=True)

    class Meta:
        model = Nomination
        fields = ["id", "title", "order", "winners"]
        read_only_fields = ["order"]


class ForumEditionListSerializer(BaseModelSerializer):
    nominations_count = serializers.IntegerField(read_only=True)
    winners_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ForumEdition
        fields = [
            "id", "year", "results_year", "title", "dates", "location", "cover", "nominations_count", "winners_count",
            "is_published", "published_at", "updated_at",
        ]


class ForumEditionSerializer(ForumEditionListSerializer):
    nominations = NominationSerializer(many=True, read_only=True)
    gallery_slug = serializers.CharField(source="gallery.slug", read_only=True, default=None)

    class Meta(ForumEditionListSerializer.Meta):
        fields = ForumEditionListSerializer.Meta.fields + ["intro", "gallery", "gallery_slug", "nominations", "created_at"]
        read_only_fields = ["created_at", "updated_at"]


class StructureWinnerSerializer(serializers.Serializer):
    level = serializers.ChoiceField(choices=Winner.Level.choices, default=Winner.Level.WINNER)
    name = serializers.CharField(max_length=400)
    note = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class StructureNominationSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=400)
    winners = StructureWinnerSerializer(many=True)


class StructureSerializer(serializers.Serializer):
    nominations = StructureNominationSerializer(many=True)
