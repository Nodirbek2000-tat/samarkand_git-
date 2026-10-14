from django.contrib import admin

from .models import Partner


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ["name", "kind", "country", "is_published", "order"]
    list_filter = ["kind", "is_published"]
