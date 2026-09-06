from django.contrib import admin

from .models import Product, Order, OrderItem, Notification

from config.admin_site import market_admin


@admin.register(Product, site=market_admin)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "category",
        "price",
        "stock",
        "created_at",
    )

    search_fields = (
        "name",
        "category",
        "description",
    )

    list_filter = (
        "category",
        "created_at",
    )


class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0

    readonly_fields = (
        "product",
        "quantity",
        "price",
    )


@admin.register(Order, site=market_admin)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer",
        "full_name",
        "total_amount",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "full_name",
        "email",
        "phone",
        "city",
    )

    readonly_fields = (
        "customer",
        "total_amount",
        "created_at",
        "updated_at",
    )

    inlines = [
        OrderItemInline
 ]  
    
# ============================================================
# NOTIFICATION ADMIN
# ============================================================

@admin.register(Notification, site=market_admin)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "message",
        "notification_type",
        "is_read",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "is_read",
        "created_at",
    )

    search_fields = (
        "user__username",
        "message",
    )

    list_editable = (
        "is_read",
    )

    ordering = (
        "-created_at",
    )