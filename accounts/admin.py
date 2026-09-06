from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from config.admin_site import market_admin


market_admin.register(
    User,
    UserAdmin
)
