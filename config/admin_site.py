
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.template.response import TemplateResponse
from django.urls import path

from products.models import Product, Order


class MarketHubAdminSite(AdminSite):

    site_header = "MarketHub Administration"
    site_title = "MarketHub Admin"
    index_title = "MarketHub Dashboard"

    def each_context(self, request):

        context = super().each_context(request)

        context["total_users"] = User.objects.count()
        context["total_products"] = Product.objects.count()
        context["total_orders"] = Order.objects.count()

        total_revenue = (
            Order.objects
            .exclude(status__iexact="cancelled")
            .aggregate(total=Sum("total_amount"))
            ["total"]
        ) or 0

        context["total_revenue"] = total_revenue

        context["pending_orders"] = Order.objects.filter(
            status__iexact="pending"
        ).count()

        context["processing_orders"] = Order.objects.filter(
            status__iexact="processing"
        ).count()

        context["completed_orders"] = Order.objects.filter(
            status__iexact="completed"
        ).count()

        context["cancelled_orders"] = Order.objects.filter(
            status__iexact="cancelled"
        ).count()

        return context

    def analytics_view(self, request):

        total_users = User.objects.count()
        total_products = Product.objects.count()
        total_orders = Order.objects.count()

        total_revenue = (
            Order.objects
            .exclude(status__iexact="cancelled")
            .aggregate(total=Sum("total_amount"))
            ["total"]
        ) or 0

        pending_orders = Order.objects.filter(
            status__iexact="pending"
        ).count()

        processing_orders = Order.objects.filter(
            status__iexact="processing"
        ).count()

        completed_orders = Order.objects.filter(
            status__iexact="completed"
        ).count()

        cancelled_orders = Order.objects.filter(
            status__iexact="cancelled"
        ).count()

        recent_orders = Order.objects.order_by(
            "-created_at"
        )[:10]

        order_status_data = (
            Order.objects
            .values("status")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        context = {
            **self.each_context(request),

            "title": "MarketHub Analytics",

            "total_users": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": total_revenue,

            "pending_orders": pending_orders,
            "processing_orders": processing_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,

            "recent_orders": recent_orders,
            "order_status_data": order_status_data,
        }

        return TemplateResponse(
            request,
            "products/analytics.html",
            context,
        )

    def get_urls(self):

        urls = super().get_urls()

        custom_urls = [
            path(
                "analytics/",
                self.admin_view(self.analytics_view),
                name="analytics",
            ),
        ]

        return custom_urls + urls


market_admin = MarketHubAdminSite(
    name="market_admin"
)
