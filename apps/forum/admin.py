from django.contrib import admin

from .models import ForumEdition, Nomination, Winner


class WinnerInline(admin.TabularInline):
    model = Winner
    extra = 0


@admin.register(Nomination)
class NominationAdmin(admin.ModelAdmin):
    list_display = ["title", "edition", "order"]
    list_filter = ["edition"]
    inlines = [WinnerInline]


class NominationInline(admin.TabularInline):
    model = Nomination
    extra = 0
    show_change_link = True


@admin.register(ForumEdition)
class ForumEditionAdmin(admin.ModelAdmin):
    list_display = ["year", "title", "dates", "is_published"]
    inlines = [NominationInline]
