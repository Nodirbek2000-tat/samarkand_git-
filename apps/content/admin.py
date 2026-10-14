from django.contrib import admin

from .models import Announcement, Film, Gallery, GalleryImage, News, NewsImage


class NewsImageInline(admin.TabularInline):
    model = NewsImage
    extra = 0


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "is_published", "published_at", "views"]
    list_filter = ["category", "is_published", "is_featured"]
    search_fields = ["title", "excerpt", "body"]
    inlines = [NewsImageInline]


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ["title", "company", "is_published", "order"]
    search_fields = ["title", "company"]


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "event_date", "is_published"]
    list_filter = ["kind", "is_published"]
    search_fields = ["title", "excerpt"]


class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    extra = 0


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ["title", "event_date", "is_published"]
    search_fields = ["title"]
    inlines = [GalleryImageInline]
