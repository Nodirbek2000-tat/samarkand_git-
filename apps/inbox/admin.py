from django.contrib import admin

from .models import Appeal, CooperationRequest, MemberApplication


class InboxAdmin(admin.ModelAdmin):
    list_filter = ["status"]
    readonly_fields = ["ip_address", "created_at"]


@admin.register(Appeal)
class AppealAdmin(InboxAdmin):
    list_display = ["full_name", "kind", "subject", "status", "created_at"]
    search_fields = ["full_name", "phone", "email", "message"]


@admin.register(CooperationRequest)
class CooperationRequestAdmin(InboxAdmin):
    list_display = ["organization", "contact_person", "kind", "status", "created_at"]


@admin.register(MemberApplication)
class MemberApplicationAdmin(InboxAdmin):
    list_display = ["full_name", "company", "size", "status", "created_at"]
