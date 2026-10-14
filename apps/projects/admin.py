from django.contrib import admin

from .models import Project, ProjectDocument, ProjectImage, ProjectParticipant


class ImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 0


class DocumentInline(admin.TabularInline):
    model = ProjectDocument
    extra = 0


class ParticipantInline(admin.TabularInline):
    model = ProjectParticipant
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "status", "is_published", "order"]
    list_filter = ["category", "status", "is_published"]
    search_fields = ["title", "summary", "body"]
    inlines = [ParticipantInline, ImageInline, DocumentInline]
