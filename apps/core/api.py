"""Reusable DRF building blocks shared by every content app."""

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import parsers, routers, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .permissions import IsStaff, is_admin

MULTIPART = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]


class OptionalSlashRouter(routers.DefaultRouter):
    """Accept `/api/news` and `/api/news/` alike (the Next.js proxy strips trailing slashes)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = "/?"


class IdOrSlugLookupMixin:
    """`/api/news/12` (admin) and `/api/news/my-slug` (public pages) resolve the same object."""

    lookup_field = "pk"
    lookup_url_kwarg = "ref"
    lookup_value_regex = "[^/]+"
    slug_field = "slug"

    def get_object(self):
        ref = self.kwargs[self.lookup_url_kwarg]
        self.lookup_field = "pk" if str(ref).isdigit() else self.slug_field
        self.kwargs[self.lookup_field] = ref
        self.lookup_url_kwarg = self.lookup_field
        return super().get_object()


class PublishedQuerysetMixin:
    """
    Public visitors only ever see published rows.
    Staff see everything and can filter with ?status=published|draft (or force ?public=1).
    """

    published_field = "is_published"

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if not is_admin(self.request.user) or params.get("public") == "1":
            return qs.filter(**{self.published_field: True})
        state = params.get("status")
        if state == "published":
            qs = qs.filter(**{self.published_field: True})
        elif state == "draft":
            qs = qs.filter(**{self.published_field: False})
        return qs


class ReorderSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False, max_length=1000)


class ReorderMixin:
    """POST <list>/reorder {"ids": [3, 1, 2]} — persists drag-and-drop order."""

    order_field = "order"

    @extend_schema(request=ReorderSerializer, responses={204: None})
    @action(detail=False, methods=["post"], permission_classes=[IsStaff])
    def reorder(self, request, *args, **kwargs):
        ser = ReorderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ids = ser.validated_data["ids"]
        model = self.get_queryset().model
        objs = {o.pk: o for o in model._default_manager.filter(pk__in=ids)}
        with transaction.atomic():
            for index, pk in enumerate(ids):
                obj = objs.get(pk)
                if obj is not None and getattr(obj, self.order_field) != index:
                    setattr(obj, self.order_field, index)
                    obj.save(update_fields=[self.order_field])
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublishToggleMixin:
    """POST <detail>/publish {"is_published": true|false} — omit the flag to toggle."""

    @extend_schema(request=None)
    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def publish(self, request, *args, **kwargs):
        obj = self.get_object()
        value = request.data.get("is_published")
        if isinstance(value, str):
            value = value.lower() in {"1", "true", "yes"}
        obj.is_published = (not obj.is_published) if value is None else bool(value)
        obj.save()
        return Response(self.get_serializer(obj).data)


def bulk_create_images(parent, files, model, fk_name: str, field: str = "image"):
    """Create several image rows for `parent` from an uploaded file list, appended after existing ones."""
    if not files:
        raise ValidationError({"files": "Kamida bitta rasm tanlang."})
    if len(files) > 50:
        raise ValidationError({"files": "Bir martada 50 tadan ortiq rasm yuklab bo‘lmaydi."})
    start = model._default_manager.filter(**{fk_name: parent}).count()
    created = []
    with transaction.atomic():
        for offset, f in enumerate(files):
            obj = model(**{fk_name: parent, field: f, "order": start + offset})
            obj.full_clean(exclude=[fk_name])
            obj.save()
            created.append(obj)
    return created
