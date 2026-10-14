from django.contrib import admin

from .models import EditorUpload, Page, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "key", "section", "is_published", "updated_at"]
    list_filter = ["section", "is_published"]
    search_fields = ["title", "key", "body"]


admin.site.register(EditorUpload)
