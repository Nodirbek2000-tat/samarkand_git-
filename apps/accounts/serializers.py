from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers

User = get_user_model()


class MeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    telegram = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "full_name", "email", "is_staff", "is_superuser",
            "last_login", "telegram",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_telegram(self, obj):
        tg = getattr(obj, "telegram", None)
        if not tg:
            return None
        return {"phone": tg.phone, "username": tg.username, "company": tg.company, "position": tg.position}


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, trim_whitespace=False)


class CodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=12)


class ProfileSerializer(serializers.Serializer):
    """Fields a visitor may edit in their cabinet (phone comes from Telegram and stays verified)."""

    first_name = serializers.CharField(max_length=150, allow_blank=False)
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    email = serializers.EmailField(allow_blank=True, required=False)
    company = serializers.CharField(max_length=255, allow_blank=True, required=False)
    position = serializers.CharField(max_length=255, allow_blank=True, required=False)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(trim_whitespace=False)
    new_password = serializers.CharField(trim_whitespace=False, min_length=10)

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Joriy parol noto‘g‘ri.")
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context["request"].user)
        return value


ROLES = {"user": "Foydalanuvchi", "editor": "Muharrir", "admin": "Administrator"}


def role_of(user) -> str:
    if user.is_superuser:
        return "admin"
    return "editor" if user.is_staff else "user"


class UserAdminSerializer(serializers.ModelSerializer):
    """
    Every account in one list. `role` is the only lever for rights:
    user (site visitor, cabinet only) · editor (content) · admin (everything).
    Telegram-registered people keep signing in with the bot code; staff created here get a password.
    """

    role = serializers.ChoiceField(choices=list(ROLES), required=False)
    role_label = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=False, trim_whitespace=False)
    full_name = serializers.SerializerMethodField()
    has_password = serializers.SerializerMethodField()
    telegram = serializers.SerializerMethodField()
    submissions = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "full_name", "email", "role", "role_label",
            "is_active", "has_password", "telegram", "submissions", "last_login", "date_joined", "password",
        ]
        read_only_fields = ["last_login", "date_joined"]
        extra_kwargs = {"username": {"required": False}}

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data["role"] = role_of(obj)
        return data

    def get_role_label(self, obj):
        return ROLES[role_of(obj)]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_has_password(self, obj):
        return obj.has_usable_password()

    def get_telegram(self, obj):
        tg = getattr(obj, "telegram", None)
        if not tg:
            return None
        return {
            "phone": tg.phone, "username": tg.username, "company": tg.company, "position": tg.position,
            "bot_blocked": tg.is_blocked_bot, "registered_at": tg.created_at,
        }

    def validate(self, attrs):
        request = self.context["request"]
        me = self.instance is not None and self.instance.pk == request.user.pk
        role = attrs.get("role")

        if self.instance is None:
            if not attrs.get("username"):
                raise serializers.ValidationError({"username": "Login majburiy."})
            if not attrs.get("password"):
                raise serializers.ValidationError({"password": "Yangi xodim uchun parol majburiy."})
            if role in (None, "user"):
                attrs["role"] = "editor"  # accounts created here are staff by definition
        if attrs.get("password"):
            password_validation.validate_password(attrs["password"], self.instance)

        if me and ((role and role != role_of(self.instance)) or attrs.get("is_active") is False):
            raise serializers.ValidationError("O‘z huquqingizni o‘zgartira yoki o‘zingizni bloklay olmaysiz.")

        # never leave the site without an active administrator
        if self.instance is not None and self.instance.is_superuser:
            losing = (role and role != "admin") or attrs.get("is_active") is False
            others = User.objects.filter(is_superuser=True, is_active=True).exclude(pk=self.instance.pk).exists()
            if losing and not others:
                raise serializers.ValidationError("Bu oxirgi administrator — avval boshqa administrator tayinlang.")
        return attrs

    @staticmethod
    def _apply_role(user, role):
        user.is_staff = role in ("editor", "admin")
        user.is_superuser = role == "admin"

    def create(self, validated):
        password = validated.pop("password")
        role = validated.pop("role")
        user = User(**validated)
        self._apply_role(user, role)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated):
        password = validated.pop("password", None)
        role = validated.pop("role", None)
        for key, value in validated.items():
            setattr(instance, key, value)
        if role:
            self._apply_role(instance, role)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
