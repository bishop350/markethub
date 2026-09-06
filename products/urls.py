from django.urls import path
from . import views


urlpatterns = [

    path("", views.home, name="home"),

    path(
        "products/",
        views.product_list,
        name="product_list"
    ),

    path(
        "products/<int:product_id>/",
        views.product_detail,
        name="product_detail"
    ),

    # =========================
    # CART
    # =========================

    path(
        "cart/",
        views.cart,
        name="cart"
    ),

    path(
        "cart/add/<int:product_id>/",
        views.add_to_cart,
        name="add_to_cart"
    ),

    path(
        "cart/remove/<int:product_id>/",
        views.remove_from_cart,
        name="remove_from_cart"
    ),

    path(
        "cart/increase/<int:product_id>/",
        views.increase_cart,
        name="increase_cart"
    ),

    path(
        "cart/decrease/<int:product_id>/",
        views.decrease_cart,
        name="decrease_cart"
    ),

    # =========================
    # CHECKOUT
    # =========================

    path(
        "checkout/",
        views.checkout,
        name="checkout"
    ),

    path(
        "order-success/<int:order_id>/",
        views.order_success,
        name="order_success"
    ),

    # =========================
    # CUSTOMER ORDERS
    # =========================

    path(
        "my-orders/",
        views.my_orders,
        name="my_orders"
    ),

    path(
        "my-orders/<int:order_id>/",
        views.order_detail,
        name="order_detail"
    ),

    # =========================
    # CUSTOMER DASHBOARD
    # =========================

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    # =========================
    # NOTIFICATIONS
    # =========================

    path(
        "notifications/",
        views.notifications,
        name="notifications"
    ),

    path(
        "notifications/read/<int:notification_id>/",
        views.mark_notification_read,
        name="mark_notification_read"
    ),

    path(
        "notifications/read-all/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read"
    ),

    # =========================
    # ADMIN DASHBOARD
    # =========================

    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

    # =========================
    # ADMIN ANALYTICS
    # =========================

    path(
        "admin-dashboard/analytics/",
        views.admin_analytics,
        name="admin_analytics"
    ),

    # =========================
    # ADMIN PRODUCTS
    # =========================

    path(
        "admin-dashboard/products/",
        views.admin_products,
        name="admin_products"
    ),

    path(
        "admin-dashboard/products/add/",
        views.admin_add_product,
        name="admin_add_product"
    ),

    path(
        "admin-dashboard/products/edit/<int:product_id>/",
        views.admin_edit_product,
        name="admin_edit_product"
    ),

    path(
        "admin-dashboard/products/delete/<int:product_id>/",
        views.admin_delete_product,
        name="admin_delete_product"
    ),

    # =========================
    # ADMIN ORDERS
    # =========================

    path(
        "admin-dashboard/orders/",
        views.admin_orders,
        name="admin_orders"
    ),

    path(
        "admin-dashboard/order/<int:order_id>/",
        views.admin_order_detail,
        name="admin_order_detail"
    ),
]