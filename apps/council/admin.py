from django.contrib import admin

from .models import BoardMember, CouncilMember, Leader, Meeting, Recognition


@admin.register(CouncilMember)
class CouncilMemberAdmin(admin.ModelAdmin):
    list_display = ["full_name", "company", "position", "is_active", "order"]
    search_fields = ["full_name", "company"]
    list_editable = ["order"]


@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    list_display = ["full_name", "role", "is_active", "order"]
    list_editable = ["order"]


@admin.register(Leader)
class LeaderAdmin(admin.ModelAdmin):
    list_display = ["full_name", "position", "is_active", "order"]


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "host_company", "is_published"]


@admin.register(Recognition)
class RecognitionAdmin(admin.ModelAdmin):
    list_display = ["full_name", "award", "year", "is_published"]
