from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart, Orders
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
import razorpay

# Create your views here.


def index(req):
    allproducts = Product.objects.all()
    context = {"allproducts": allproducts}
    return render(req, "index.html", context)


class ProductRegister(CreateView):
    model = Product
    fields = "_all_"
    success_url = "/Productlist"


class Productlist(ListView):
    model = Product


def signup(req):
    if req.method == "POST":
        uname = req.POST["uname"]
        upass = req.POST["upass"]
        ucpass = req.POST["ucpass"]
        context = {}

        if uname == "" or upass == "" or ucpass == "":
            context["errmsg"] = "Field can't be empty"
            return render(req, "signup.html", context)
        elif upass != ucpass:
            context["errmsg"] = "Password and confirm password doesn't match"
            return render(req, "signup.html", context)
        else:
            try:
                userdata = User.objects.create(username=uname, password=upass)
                userdata.set_password(upass)
                userdata.save()
                return redirect("/signin")
            except:
                context["errmsg"] = "User Already exists"
                return render(req, "signup.html", context)
    else:
        context = {}
        context["errmsg"] = ""
        return render(req, "signup.html", context)


def signin(req):
    if req.method == "POST":
        uname = req.POST["uname"]
        upass = req.POST["upass"]
        context = {}
        if uname == "" or upass == "":
            context["errmsg"] = "Field can't be empty"
            return render(req, "signin.html", context)
        else:
            userdata = authenticate(username=uname, password=upass)
            if userdata is not None:
                login(req, userdata)
                return redirect("/")
            else:
                context["errmsg"] = "Invalid username and password"
                return render(req, "signin.html", context)
    else:
        return render(req, "signin.html")


def userlogout(req):
    logout(req)
    return redirect("/")


def mobilelist(req):
    if req.method == "GET":
        allproducts = Product.productmanager.mobile_list()
        context = {"allproducts": allproducts}
        return render(req, "index.html", context)
    else:
        allproducts = Product.objects.all()
        context = {"allproducts": allproducts}
        return render(req, "index.html", context)


def electronicslist(req):
    if req.method == "GET":
        allproducts = Product.productmanager.electronics_list()
        context = {"allproducts": allproducts}
        return render(req, "index.html", context)
    else:
        allproducts = Product.objects.all()
        context = {"allproducts": allproducts}
        return render(req, "index.html", context)


def showpricerange(req):
    if req.method == "GET":
        return render(req, "index.html")
    else:
        r1 = req.POST.get("min")
        r2 = req.POST.get("max")
        if r1 is not None and r2 is not None and r1.isdigit() and r2.isdigit():
            allproducts = Product.productmanager.pricerange(r1, r2)
            context = {"allproducts": allproducts}
            return render(req, "index.html", context)
        else:
            allproducts = Product.objects.all()
            context = {"allproducts": allproducts}
            return render(req, "index.html", context)


def sortingbyprice(req):
    sortoption = req.GET.get("sort")
    if sortoption == "low_to_high":
        allproducts = Product.objects.order_by("price")  # asc order
    elif sortoption == "high_to_low":
        allproducts = Product.objects.order_by("-price")  # desc order
    else:
        allproducts = Product.objects.all()

    context = {"allproducts": allproducts}
    return render(req, "index.html", context)


from django.contrib import messages
from django.db.models import Q


def searchproduct(req):
    query = req.GET.get("q")
    if query:
        allproducts = Product.objects.filter(
            Q(productname__icontains=query)
            | Q(category__icontains=query)
            | Q(description__icontains=query)
        )
        if len(allproducts) == 0:
            messages.error(req, "No result found!!!")
    else:
        allproducts = Product.objects.all()

    context = {"allproducts": allproducts}
    return render(req, "index.html", context)


def showcarts(req):
    user = req.user
    allcarts = Cart.objects.filter(userid=user.id)
    totalamount = 0

    for x in allcarts:
        totalamount += x.productid.price * x.qty
    totalitems = len(allcarts)

    if req.user.is_authenticated:
        context = {
            "allcarts": allcarts,
            "username": user,
            "totalamount": totalamount,
            "totalitems": totalitems,
        }
    else:
        context = {
            "allcarts": allcarts,
            "totalamount": totalamount,
            "totalitems": totalitems,
        }

    return render(req, "showcarts.html", context)


def updateqty(req, qv, productid):
    allcarts = Cart.objects.filter(productid=productid)
    if qv == 1:
        total = allcarts[0].qty + 1
        allcarts.update(qty=total)
    else:
        if allcarts[0].qty > 1:
            total = allcarts[0].qty - 1
            allcarts.update(qty=total)
        else:
            allcarts = Cart.objects.filter(productid=productid)
            allcarts.delete()

    return redirect("/showcarts")


def removecart(req, productid):
    user = req.user
    cartitems = Cart.objects.get(productid=productid, userid=user.id)
    cartitems.delete()
    return redirect("/showcarts")


def addcart(req, productid):
    if req.user.is_authenticated:
        user = req.user
    else:
        user = None

    allproducts = get_object_or_404(Product, productid=productid)
    cartitem, created = Cart.objects.get_or_create(productid=allproducts, userid=user)
    if not created:
        cartitem.qty += 1
    else:
        cartitem.qty = 1
    cartitem.save()
    return redirect("/showcarts")


import random
from django.conf import settings
from django.core.mail import send_mail


def payment(req):
    if req.user.is_authenticated:
        user = req.user
        allcarts = Cart.objects.filter(userid=user.id)
        totalamount = 0
        for x in allcarts:
            orderid = random.randrange(1000, 90000)
            orderdata = Orders.objects.create(
                orderid=orderid, productid=x.productid, userid=x.userid, qty=x.qty
            )
            orderdata.save()
            totalamount +=  x.qty*x.productid.price 
            x.delete()
        oid=orderid

        client = razorpay.Client(
            auth=("rzp_test_wH0ggQnd7iT3nB", "eZseshY3oSsz2fcHZkTiSlCm")
        )
        data = {"amount": totalamount * 100, "currency": "INR", "receipt": str(oid)}
        payment = client.order.create(data=data)
        subject=f"flipkart-Payment Status for your order={orderid}"
        msg=f"hii {user},thak you for using our services.\ntotal amount paid=rs.{totalamount}/-"
        emailfrom=settings.EMAIL_HOST_USER
        receiver=[user,user.email]
        send_mail(subject,msg,emailfrom,receiver)




        context = {"data": payment, "amount": payment, "username": user}
        return render(req, "payment.html", context)
    else:
        return redirect("/signin")
    

def showorders(req):
    orderdata=Orders.objects.filter(userid=req.user)
    totalamount=0
    for x in orderdata:
        totalamount = x.qty*x.productid.price
    context={"username":req.user,"orderdata":orderdata,"totalamount":totalamount}
    return render(req,"showorders.html",context)
