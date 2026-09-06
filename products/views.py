from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, F, Sum, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Product, Order, OrderItem, Notification


# ============================================================
# HOME
# ============================================================

def home(request):
    products = Product.objects.all().order_by("-created_at")[:8]

    return render(
        request,
        "products/home.html",
        {
            "products": products,
        },
    )


# ============================================================
# PRODUCTS
# ============================================================

def product_list(request):
    products = Product.objects.all().order_by("-created_at")

    search = request.GET.get("search", "")
    category = request.GET.get("category", "")

    if search:
        products = products.filter(name__icontains=search)

    if category:
        products = products.filter(category=category)

    categories = (
        Product.objects
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "categories": categories,
            "search": search,
            "selected_category": category,
        },
    )


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    return render(
        request,
        "products/product_detail.html",
        {
            "product": product,
        },
    )


# ============================================================
# CART
# ============================================================

def cart(request):
    cart_data = request.session.get("cart", {})

    cart_items = []
    total = 0

    for product_id, quantity in cart_data.items():

        product = get_object_or_404(Product, id=int(product_id))

        subtotal = product.price * quantity
        total += subtotal

        cart_items.append(
            {
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal,
            }
        )

    return render(
        request,
        "products/cart.html",
        {
            "cart_items": cart_items,
            "total": total,
        },
    )


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart_data = request.session.get("cart", {})

    product_id = str(product_id)

    current_quantity = cart_data.get(product_id, 0)

    if current_quantity >= product.stock:
        messages.error(
            request,
            "Sorry, there is not enough stock available."
        )
        return redirect("product_detail", product_id=product.id)

    cart_data[product_id] = current_quantity + 1

    request.session["cart"] = cart_data
    request.session.modified = True

    messages.success(
        request,
        f"{product.name} added to your cart."
    )

    return redirect("cart")


def remove_from_cart(request, product_id):
    cart_data = request.session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart_data:
        del cart_data[product_id]

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


def increase_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart_data = request.session.get("cart", {})

    product_id = str(product_id)

    current_quantity = cart_data.get(product_id, 0)

    if current_quantity >= product.stock:
        messages.error(
            request,
            "You cannot add more than the available stock."
        )
        return redirect("cart")

    cart_data[product_id] = current_quantity + 1

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


def decrease_cart(request, product_id):
    cart_data = request.session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart_data:

        if cart_data[product_id] > 1:
            cart_data[product_id] -= 1
        else:
            del cart_data[product_id]

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


# ============================================================
# CHECKOUT
# ============================================================

@login_required
def checkout(request):

    cart_data = request.session.get("cart", {})

    if not cart_data:
        messages.warning(request, "Your cart is empty.")
        return redirect("cart")

    cart_items = []
    total = 0

    for product_id, quantity in cart_data.items():

        product = get_object_or_404(Product, id=int(product_id))

        if quantity > product.stock:
            messages.error(
                request,
                f"Not enough stock for {product.name}."
            )
            return redirect("cart")

        subtotal = product.price * quantity
        total += subtotal

        cart_items.append(
            {
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal,
            }
        )

    if request.method == "POST":

        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()

        if not all(
            [
                full_name,
                email,
                phone,
                address,
                city,
            ]
        ):
            messages.error(
                request,
                "Please complete all checkout fields."
            )

            return render(
                request,
                "products/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                },
            )

        order = Order.objects.create(
            customer=request.user,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            total_amount=total,
            status="pending",
        )

        for item in cart_items:

            product = item["product"]
            quantity = item["quantity"]

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price,
            )

            product.stock -= quantity
            product.save()

        # Customer notification
        Notification.objects.create(
            user=request.user,
            message=(
                f"Your order #{order.id} has been placed successfully."
            ),
            notification_type="order",
        )

        # Notify staff members
        staff_users = User.objects.filter(
            is_staff=True,
            is_active=True,
        )

        for staff_user in staff_users:

            Notification.objects.create(
                user=staff_user,
                message=(
                    f"New order #{order.id} received from "
                    f"{order.full_name}."
                ),
                notification_type="order",
            )

        request.session["cart"] = {}
        request.session.modified = True

        return redirect(
            "order_success",
            order_id=order.id,
        )

    return render(
        request,
        "products/checkout.html",
        {
            "cart_items": cart_items,
            "total": total,
        },
    )


@login_required
def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.user,
    )

    return render(
        request,
        "products/order_success.html",
        {
            "order": order,
        },
    )


# ============================================================
# CUSTOMER ORDERS
# ============================================================

@login_required
def my_orders(request):

    orders = (
        Order.objects
        .filter(customer=request.user)
        .order_by("-created_at")
    )

    return render(
        request,
        "products/my_orders.html",
        {
            "orders": orders,
        },
    )


@login_required
def order_detail(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.user,
    )

    return render(
        request,
        "products/order_detail.html",
        {
            "order": order,
        },
    )


# ============================================================
# CUSTOMER DASHBOARD
# ============================================================

@login_required
def dashboard(request):

    orders = Order.objects.filter(
        customer=request.user
    )

    total_orders = orders.count()

    total_spent = (
        orders
        .exclude(status="cancelled")
        .aggregate(total=Sum("total_amount"))
        ["total"]
        or 0
    )

    recent_orders = orders.order_by(
        "-created_at"
    )[:5]

    return render(
        request,
        "products/dashboard.html",
        {
            "total_orders": total_orders,
            "total_spent": total_spent,
            "recent_orders": recent_orders,
        },
    )


# ============================================================
# STAFF ACCESS
# ============================================================

def staff_required(view_function):

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if not request.user.is_staff:
            return HttpResponseForbidden(
                "You do not have permission to access this page."
            )

        return view_function(
            request,
            *args,
            **kwargs,
        )

    return wrapper


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@staff_required
def admin_dashboard(request):

    total_products = Product.objects.count()

    total_orders = Order.objects.count()

    total_customers = User.objects.filter(
        is_staff=False
    ).count()

    pending_orders = Order.objects.filter(
        status="pending"
    ).count()

    processing_orders = Order.objects.filter(
        status="processing"
    ).count()

    shipped_orders = Order.objects.filter(
        status="shipped"
    ).count()

    delivered_orders = Order.objects.filter(
        status="delivered"
    ).count()

    return render(
        request,
        "products/admin_dashboard.html",
        {
            "total_products": total_products,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "pending_orders": pending_orders,
            "processing_orders": processing_orders,
            "shipped_orders": shipped_orders,
            "delivered_orders": delivered_orders,
        },
    )


# ============================================================
# SALES ANALYTICS
# ============================================================

@staff_required
def admin_analytics(request):

    # --------------------------------------------------------
    # BASIC STATISTICS
    # --------------------------------------------------------

    total_orders = Order.objects.count()

    total_products = Product.objects.count()

    total_customers = User.objects.filter(
        is_staff=False
    ).count()

    # Cancelled orders are excluded from revenue.
    total_revenue = (
        Order.objects
        .exclude(status="cancelled")
        .aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    # --------------------------------------------------------
    # ORDER STATUS
    # --------------------------------------------------------

    pending_orders = Order.objects.filter(
        status="pending"
    ).count()

    processing_orders = Order.objects.filter(
        status="processing"
    ).count()

    shipped_orders = Order.objects.filter(
        status="shipped"
    ).count()

    delivered_orders = Order.objects.filter(
        status="delivered"
    ).count()

    cancelled_orders = Order.objects.filter(
        status="cancelled"
    ).count()

    # --------------------------------------------------------
    # SALES FOR LAST 6 MONTHS
    # --------------------------------------------------------

    today = timezone.localdate()

    monthly_queryset = (
        Order.objects
        .exclude(status="cancelled")
        .filter(
            created_at__date__gte=(
                today.replace(
                    day=1
                )
            )
        )
        .annotate(
            month=TruncMonth("created_at")
        )
        .values("month")
        .annotate(
            amount=Sum("total_amount")
        )
        .order_by("month")
    )

    monthly_lookup = {
        item["month"].strftime("%Y-%m"): item["amount"]
        for item in monthly_queryset
    }

    monthly_sales = []

    # Build six months including the current month.
    year = today.year
    month = today.month

    for _ in range(6):

        month_key = f"{year:04d}-{month:02d}"

        month_date = datetime(
            year,
            month,
            1,
        )

        amount = monthly_lookup.get(
            month_key,
            0
        ) or 0

        monthly_sales.append(
            {
                "label": month_date.strftime("%b"),
                "amount": amount,
                "height": 20,
            }
        )

        month -= 1

        if month == 0:
            month = 12
            year -= 1

    monthly_sales.reverse()

    # --------------------------------------------------------
    # BAR HEIGHTS
    # --------------------------------------------------------

    max_amount = max(
        [
            float(item["amount"])
            for item in monthly_sales
        ],
        default=0,
    )

    for item in monthly_sales:

        if max_amount > 0:

            item["height"] = max(
                20,
                int(
                    (
                        float(item["amount"])
                        / max_amount
                    )
                    * 190
                ),
            )

        else:
            item["height"] = 20

    # --------------------------------------------------------
    # BEST SELLING PRODUCTS
    # --------------------------------------------------------

    best_products = (
        OrderItem.objects
        .filter(
            order__status__in=[
                "pending",
                "processing",
                "shipped",
                "delivered",
            ]
        )
        .values(
            "product__name",
            "product__category",
        )
        .annotate(
            total_quantity=Sum("quantity"),
            total_revenue=Sum(
                ExpressionWrapper(
                    F("quantity") * F("price"),
                    output_field=DecimalField(
                        max_digits=12,
                        decimal_places=2,
                    ),
                )
            ),
        )
        .order_by("-total_quantity")[:10]
    )

    # --------------------------------------------------------
    # RECENT ORDERS
    # --------------------------------------------------------

    recent_orders = (
        Order.objects
        .select_related("customer")
        .order_by("-created_at")[:10]
    )

    # --------------------------------------------------------
    # SEND DATA TO TEMPLATE
    # --------------------------------------------------------

    context = {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_products": total_products,

        "pending_orders": pending_orders,
        "processing_orders": processing_orders,
        "shipped_orders": shipped_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,

        "monthly_sales": monthly_sales,

        "best_products": best_products,

        "recent_orders": recent_orders,
    }

    return render(
        request,
        "products/admin_analytics.html",
        context,
    )


# ============================================================
# ADMIN PRODUCT MANAGEMENT
# ============================================================

@staff_required
def admin_products(request):

    products = Product.objects.all().order_by(
        "-created_at"
    )

    return render(
        request,
        "products/admin_products.html",
        {
            "products": products,
        },
    )


@staff_required
def admin_add_product(request):

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        category = request.POST.get("category", "").strip()
        price = request.POST.get("price", "").strip()
        stock = request.POST.get("stock", "").strip()
        description = request.POST.get(
            "description",
            ""
        ).strip()

        image = request.FILES.get("image")

        if not all(
            [
                name,
                category,
                price,
                stock,
            ]
        ):
            messages.error(
                request,
                "Please fill in all required fields."
            )

            return render(
                request,
                "products/admin_add_product.html",
            )

        Product.objects.create(
            name=name,
            category=category,
            price=price,
            stock=stock,
            description=description,
            image=image,
        )

        messages.success(
            request,
            "Product added successfully."
        )

        return redirect("admin_products")

    return render(
        request,
        "products/admin_add_product.html",
    )


@staff_required
def admin_edit_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    if request.method == "POST":

        product.name = request.POST.get(
            "name",
            ""
        ).strip()

        product.category = request.POST.get(
            "category",
            ""
        ).strip()

        product.price = request.POST.get(
            "price",
            ""
        ).strip()

        product.stock = request.POST.get(
            "stock",
            ""
        ).strip()

        product.description = request.POST.get(
            "description",
            ""
        ).strip()

        if request.FILES.get("image"):
            product.image = request.FILES.get(
                "image"
            )

        product.save()

        messages.success(
            request,
            "Product updated successfully."
        )

        return redirect("admin_products")

    return render(
        request,
        "products/admin_edit_product.html",
        {
            "product": product,
        },
    )


@staff_required
def admin_delete_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    if request.method == "POST":

        product.delete()

        messages.success(
            request,
            "Product deleted successfully."
        )

    return redirect("admin_products")


# ============================================================
# ADMIN ORDER MANAGEMENT
# ============================================================

@staff_required
def admin_orders(request):

    orders = (
        Order.objects
        .select_related("customer")
        .order_by("-created_at")
    )

    return render(
        request,
        "products/admin_orders.html",
        {
            "orders": orders,
        },
    )


@staff_required
def admin_order_detail(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
    )

    if request.method == "POST":

        old_status = order.status

        new_status = request.POST.get(
            "status"
        )

        valid_statuses = dict(
            Order.STATUS_CHOICES
        )

        if new_status in valid_statuses:

            order.status = new_status
            order.save()

            if old_status != new_status:

                Notification.objects.create(
                    user=order.customer,
                    message=(
                        f"Your order #{order.id} status "
                        f"has been updated to "
                        f"{order.get_status_display()}."
                    ),
                    notification_type="shipping",
                )

                messages.success(
                    request,
                    "Order status updated successfully."
                )

        return redirect(
            "admin_order_detail",
            order_id=order.id,
        )

    return render(
        request,
        "products/admin_order_detail.html",
        {
            "order": order,
        },
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

@login_required
def notifications(request):

    user_notifications = (
        Notification.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    return render(
        request,
        "products/notifications.html",
        {
            "notifications": user_notifications,
        },
    )


@login_required
def mark_notification_read(
    request,
    notification_id
):

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user,
    )

    notification.is_read = True
    notification.save()

    return redirect("notifications")


@login_required
def mark_all_notifications_read(request):

    Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).update(
        is_read=True
    )

    return redirect("notifications")