from django.conf import settings
from django.views.static import serve
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.accounts.views import UserAdminViewSet
from apps.content import views as content
from apps.core import views as core
from apps.core.api import OptionalSlashRouter
from apps.core.dashboard import DashboardView
from apps.core.search import SearchView
from apps.council import views as council
from apps.forum.views import ForumEditionViewSet
from apps.inbox import views as inbox
from apps.partners.views import PartnerViewSet
from apps.projects import views as projects

router = OptionalSlashRouter()
# content
router.register("news", content.NewsViewSet, basename="news")
router.register("news-images", content.NewsImageViewSet, basename="news-image")
router.register("films", content.FilmViewSet, basename="film")
router.register("announcements", content.AnnouncementViewSet, basename="announcement")
router.register("galleries", content.GalleryViewSet, basename="gallery")
router.register("gallery-images", content.GalleryImageViewSet, basename="gallery-image")
# projects
router.register("projects", projects.ProjectViewSet, basename="project")
router.register("project-images", projects.ProjectImageViewSet, basename="project-image")
router.register("project-documents", projects.ProjectDocumentViewSet, basename="project-document")
router.register("project-participants", projects.ProjectParticipantViewSet, basename="project-participant")
# council
router.register("council-members", council.CouncilMemberViewSet, basename="council-member")
router.register("board-members", council.BoardMemberViewSet, basename="board-member")
router.register("leaders", council.LeaderViewSet, basename="leader")
router.register("meetings", council.MeetingViewSet, basename="meeting")
router.register("recognitions", council.RecognitionViewSet, basename="recognition")
# forum, partners, pages
router.register("forum", ForumEditionViewSet, basename="forum")
router.register("partners", PartnerViewSet, basename="partner")
router.register("pages", core.PageViewSet, basename="page")
# inbox (public POST, administrators read)
router.register("appeals", inbox.AppealViewSet, basename="appeal")
router.register("cooperation-requests", inbox.CooperationRequestViewSet, basename="cooperation-request")
router.register("member-applications", inbox.MemberApplicationViewSet, basename="member-application")
# accounts
router.register("admin/users", UserAdminViewSet, basename="admin-user")

api = [
    re_path(r"^settings/?$", core.SiteSettingsView.as_view(), name="site-settings"),
    re_path(r"^dashboard/?$", DashboardView.as_view(), name="dashboard"),
    re_path(r"^search/?$", SearchView.as_view(), name="search"),
    re_path(r"^uploads/editor/?$", core.EditorUploadView.as_view(), name="editor-upload"),
    path("", include("apps.accounts.urls")),
    re_path(r"^schema/?$", SpectacularAPIView.as_view(), name="schema"),
    re_path(r"^docs/?$", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("", include(router.urls)),
]

admin.site.site_header = "Yangi Samarqand — zaxira boshqaruv paneli"
admin.site.site_title = "Yangi Samarqand"
admin.site.index_title = "Ma’lumotlar bazasi"

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/", include(api)),
]

if settings.DEBUG or settings.SERVE_MEDIA:
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]
