from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.api import (
    MULTIPART,
    IdOrSlugLookupMixin,
    PublishedQuerysetMixin,
    PublishToggleMixin,
    ReorderMixin,
    bulk_create_images,
)
from apps.core.permissions import IsStaff

from .models import Project, ProjectDocument, ProjectImage, ProjectParticipant
from .serializers import (
    ProjectDocumentSerializer,
    ProjectImageSerializer,
    ProjectListSerializer,
    ProjectParticipantSerializer,
    ProjectSerializer,
)


class ProjectViewSet(IdOrSlugLookupMixin, PublishedQuerysetMixin, PublishToggleMixin, ReorderMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    parser_classes = MULTIPART
    filterset_fields = ["category", "status", "is_featured", "is_published"]
    search_fields = ["title", "summary", "body", "metrics"]
    ordering_fields = ["order", "created_at", "title"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action != "list":
            qs = qs.prefetch_related("images", "documents", "participants")
        categories = self.request.query_params.get("categories")
        if categories:
            qs = qs.filter(category__in=categories.split(","))
        return qs

    def get_serializer_class(self):
        return ProjectListSerializer if self.action == "list" else ProjectSerializer

    @extend_schema(request={"multipart/form-data": {"type": "object", "properties": {"files": {"type": "array"}}}})
    @action(detail=True, methods=["post"], permission_classes=[IsStaff], url_path="images")
    def upload_images(self, request, *args, **kwargs):
        project = self.get_object()
        created = bulk_create_images(project, request.FILES.getlist("files"), ProjectImage, "project")
        return Response(ProjectImageSerializer(created, many=True).data, status=201)

    @extend_schema(request={"multipart/form-data": {"type": "object", "properties": {"files": {"type": "array"}}}})
    @action(detail=True, methods=["post"], permission_classes=[IsStaff], url_path="documents")
    def upload_documents(self, request, *args, **kwargs):
        project = self.get_object()
        files = request.FILES.getlist("files")
        if not files:
            raise ValidationError({"files": "Kamida bitta fayl tanlang."})
        start = project.documents.count()
        created = []
        with transaction.atomic():
            for i, f in enumerate(files[:20]):
                title = f.name.rsplit(".", 1)[0][:255]
                doc = ProjectDocument(project=project, title=title, file=f, order=start + i)
                doc.full_clean(exclude=["project"])
                doc.save()
                created.append(doc)
        return Response(ProjectDocumentSerializer(created, many=True).data, status=201)


class ProjectImageViewSet(ReorderMixin, viewsets.ModelViewSet):
    queryset = ProjectImage.objects.all()
    serializer_class = ProjectImageSerializer
    permission_classes = [IsStaff]
    parser_classes = MULTIPART
    filterset_fields = ["project"]
    pagination_class = None


class ProjectDocumentViewSet(ReorderMixin, viewsets.ModelViewSet):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    permission_classes = [IsStaff]
    parser_classes = MULTIPART
    filterset_fields = ["project"]
    pagination_class = None


class ProjectParticipantViewSet(ReorderMixin, viewsets.ModelViewSet):
    """Readable publicly (e.g. Siyob canal initiators); editable by staff."""

    queryset = ProjectParticipant.objects.select_related("project")
    serializer_class = ProjectParticipantSerializer
    filterset_fields = ["project", "project__slug"]
    search_fields = ["company", "person"]
    pagination_class = None
