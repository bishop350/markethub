
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from .admin_site import market_admin


urlpatterns = [

    # ==========================================
    # MARKET HUB ADMIN
    # ==========================================

    path(
        "admin/",
        market_admin.urls
    ),

    # ==========================================
    # MARKETPLACE
    # ==========================================

    path(
        "",
        include("products.urls")
    ),

    # ==========================================
    # ACCOUNTS
    # ==========================================

    path(
        "accounts/",
        include("accounts.urls")
    ),

]


# ==============================================
# MEDIA FILES
# ==============================================

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
