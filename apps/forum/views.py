from django.db import transaction
from django.db.models import Count, Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.api import MULTIPART, PublishedQuerysetMixin, PublishToggleMixin
from apps.core.permissions import IsStaff

from .models import ForumEdition, Nomination, Winner
from .serializers import ForumEditionListSerializer, ForumEditionSerializer, StructureSerializer


class ForumEditionViewSet(PublishedQuerysetMixin, PublishToggleMixin, viewsets.ModelViewSet):
    """Addressed by forum year: /api/forum/2024."""

    parser_classes = MULTIPART
    lookup_field = "year"
    search_fields = ["title", "intro", "nominations__title", "nominations__winners__name"]
    ordering_fields = ["year"]
    pagination_class = None

    def get_queryset(self):
        self.queryset = ForumEdition.objects.annotate(
            nominations_count=Count("nominations", distinct=True),
            winners_count=Count("nominations__winners", distinct=True),
        ).select_related("gallery").order_by("-year")
        qs = super().get_queryset()
        if self.action != "list":
            qs = qs.prefetch_related(
                Prefetch("nominations", queryset=Nomination.objects.prefetch_related("winners"))
            )
        return qs.distinct() if self.request.query_params.get("search") else qs

    def get_serializer_class(self):
        return ForumEditionListSerializer if self.action == "list" else ForumEditionSerializer

    @extend_schema(request=StructureSerializer, responses={200: ForumEditionSerializer})
    @action(detail=True, methods=["put"], permission_classes=[IsStaff])
    def structure(self, request, *args, **kwargs):
        """Replace every nomination and winner of an edition in one atomic save (admin editor)."""
        edition = self.get_object()
        ser = StructureSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        with transaction.atomic():
            edition.nominations.all().delete()
            for n_index, nom in enumerate(ser.validated_data["nominations"]):
                nomination = Nomination.objects.create(edition=edition, title=nom["title"], order=n_index)
                Winner.objects.bulk_create(
                    Winner(nomination=nomination, order=w_index, **winner)
                    for w_index, winner in enumerate(nom["winners"])
                )
            edition.save(update_fields=["updated_at"])  # triggers frontend revalidation
        return Response(ForumEditionSerializer(self.get_object(), context={"request": request}).data)
