from rest_framework import serializers

from .models import Appeal, CooperationRequest, MemberApplication

ADMIN_EXTRA = [
    "status", "status_label", "admin_note", "reply", "replied_at", "handled_by", "handled_by_name",
    "account", "created_at", "updated_at",
]


class PublicFormMixin(serializers.Serializer):
    """Shared anti-spam + consent handling for every public form."""

    consent = serializers.BooleanField(write_only=True)
    hp = serializers.CharField(write_only=True, required=False, allow_blank=True)  # honeypot: must stay empty

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError("Shaxsiy ma’lumotlarni qayta ishlashga rozilik kerak.")
        return value

    def validate(self, attrs):
        if attrs.pop("hp", ""):
            raise serializers.ValidationError("So‘rov rad etildi.")
        attrs.pop("consent", None)
        email, phone = attrs.get("email"), attrs.get("phone")
        if "email" in self.fields and "phone" in self.fields and not (email or phone):
            raise serializers.ValidationError({"phone": "Telefon yoki email kiriting."})
        return attrs


class AppealPublicSerializer(PublicFormMixin, serializers.ModelSerializer):
    class Meta:
        model = Appeal
        fields = ["kind", "full_name", "phone", "email", "organization", "subject", "message", "consent", "hp"]


class CooperationPublicSerializer(PublicFormMixin, serializers.ModelSerializer):
    class Meta:
        model = CooperationRequest
        fields = ["kind", "organization", "contact_person", "phone", "email", "website", "country", "proposal", "consent", "hp"]


class MemberApplicationPublicSerializer(PublicFormMixin, serializers.ModelSerializer):
    class Meta:
        model = MemberApplication
        fields = ["full_name", "company", "position", "size", "industry", "phone", "email", "message", "consent", "hp"]


class AdminInboxMixin(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    handled_by_name = serializers.SerializerMethodField()
    account = serializers.SerializerMethodField()

    def get_handled_by_name(self, obj):
        user = obj.handled_by
        return (user.get_full_name() or user.username) if user else None

    def get_account(self, obj):
        """Registered (Telegram) sender, if any — replies reach them in the bot."""
        tg = getattr(obj.user, "telegram", None) if obj.user_id else None
        if not tg:
            return None
        return {
            "name": obj.user.get_full_name() or tg.first_name,
            "phone": tg.phone,
            "username": tg.username,
            "reachable": not tg.is_blocked_bot,
        }


class AppealAdminSerializer(AdminInboxMixin):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = Appeal
        fields = ["id", "kind", "kind_label", "full_name", "phone", "email", "organization", "subject", "message", "ip_address"] + ADMIN_EXTRA
        read_only_fields = ["ip_address", "handled_by", "replied_at", "created_at", "updated_at"]


class CooperationAdminSerializer(AdminInboxMixin):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = CooperationRequest
        fields = [
            "id", "kind", "kind_label", "organization", "contact_person", "phone", "email", "website", "country",
            "proposal", "ip_address",
        ] + ADMIN_EXTRA
        read_only_fields = ["ip_address", "handled_by", "replied_at", "created_at", "updated_at"]


class MemberApplicationAdminSerializer(AdminInboxMixin):
    size_label = serializers.CharField(source="get_size_display", read_only=True)

    class Meta:
        model = MemberApplication
        fields = [
            "id", "full_name", "company", "position", "size", "size_label", "industry", "phone", "email", "message",
            "ip_address",
        ] + ADMIN_EXTRA
        read_only_fields = ["ip_address", "handled_by", "replied_at", "created_at", "updated_at"]


class MySubmissionSerializer(serializers.Serializer):
    """What a signed-in visitor sees about their own submissions in the cabinet."""

    id = serializers.IntegerField()
    type = serializers.CharField()
    type_label = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()
    status = serializers.CharField()
    status_label = serializers.CharField()
    reply = serializers.CharField()
    replied_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
