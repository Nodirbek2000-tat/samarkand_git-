from rest_framework import viewsets

from apps.core.api import MULTIPART, IdOrSlugLookupMixin, PublishedQuerysetMixin, PublishToggleMixin, ReorderMixin

from .models import BoardMember, CouncilMember, Leader, Meeting, Recognition
from .serializers import (
    BoardMemberSerializer,
    CouncilMemberSerializer,
    LeaderSerializer,
    MeetingSerializer,
    RecognitionSerializer,
)


class ActivePeopleMixin(PublishedQuerysetMixin):
    """People lists use `is_active` as their visibility flag."""

    published_field = "is_active"


class CouncilMemberViewSet(IdOrSlugLookupMixin, ActivePeopleMixin, ReorderMixin, viewsets.ModelViewSet):
    queryset = CouncilMember.objects.all()
    serializer_class = CouncilMemberSerializer
    parser_classes = MULTIPART
    search_fields = ["full_name", "company", "position", "industry"]
    ordering_fields = ["order", "full_name"]
    pagination_class = None


class BoardMemberViewSet(IdOrSlugLookupMixin, ActivePeopleMixin, ReorderMixin, viewsets.ModelViewSet):
    queryset = BoardMember.objects.all()
    serializer_class = BoardMemberSerializer
    parser_classes = MULTIPART
    search_fields = ["full_name", "workplace"]
    ordering_fields = ["order", "full_name"]
    pagination_class = None


class LeaderViewSet(IdOrSlugLookupMixin, ActivePeopleMixin, ReorderMixin, viewsets.ModelViewSet):
    queryset = Leader.objects.all()
    serializer_class = LeaderSerializer
    parser_classes = MULTIPART
    search_fields = ["full_name", "position", "organization"]
    pagination_class = None


class MeetingViewSet(IdOrSlugLookupMixin, PublishedQuerysetMixin, PublishToggleMixin, viewsets.ModelViewSet):
    queryset = Meeting.objects.select_related("gallery")
    serializer_class = MeetingSerializer
    parser_classes = MULTIPART
    search_fields = ["title", "host_company", "location", "agenda", "outcome"]
    ordering_fields = ["date", "title"]


class RecognitionViewSet(PublishedQuerysetMixin, ReorderMixin, viewsets.ModelViewSet):
    queryset = Recognition.objects.all()
    serializer_class = RecognitionSerializer
    parser_classes = MULTIPART
    filterset_fields = ["year"]
    search_fields = ["full_name", "company", "award"]
    ordering_fields = ["year", "order", "full_name"]
    pagination_class = None
