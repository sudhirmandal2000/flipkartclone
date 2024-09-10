from django.contrib import admin
from .models import Product, Cart, Orders

# Register your models here.


class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "userid",
        "productid",
        "productname",
        "category",
        "description",
        "price",
        "images",
    ]


class CartAdmin(admin.ModelAdmin):
    list_display = ["userid", "productid", "qty"]


class OrdersAdmin(admin.ModelAdmin):
    list_display = ["orderid", "userid", "productid", "qty"]


admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Orders, OrdersAdmin)
