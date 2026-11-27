
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from library.views import dashboard


urlpatterns = [
    path("accounts/login/", auth_views.LoginView.as_view(
        template_name="registration/login.html",
        redirect_authenticated_user=True,
    ), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("admin/", admin.site.urls),

    path("api/", include("library.urls")),

    path(
        "api/ai-runtime/",
        include("ai_runtime.urls"),
    ),

    path("", dashboard, name="dashboard"),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
