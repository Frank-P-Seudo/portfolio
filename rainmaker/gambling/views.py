from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django import forms
import datetime as DT
from django.contrib import messages
from django.http import JsonResponse
import json
from .helpers import renderIndex, sortAndProcess
from creditcards.forms import CardNumberField, CardExpiryField, SecurityCodeField

from .models import User, Pool, Bet, Following

TIME_SLOTS = ((1, "00:00 - 00:59"),
              (2, "01:00 - 01:59"),
              (3, "02:00 - 02:59"),
              (4, "03:00 - 03:59"),
              (5, "04:00 - 04:59"),
              (6, "05:00 - 05:59"),
              (7, "06:00 - 06:59"),
              (8, "07:00 - 07:59"),
              (9, "08:00 - 08:59"),
              (10, "09:00 - 9:59"),
              (11, "10:00 - 10:59"),
              (12, "11:00 - 11:59"),
              (13, "12:00 - 12:59"),
              (14, "13:00 - 13:59"),
              (15, "14:00 - 14:59"),
              (16, "15:00 - 15:59"),
              (17, "16:00 - 16:59"),
              (18, "17:00 - 17:59"),
              (19, "18:00 - 18:59"),
              (20, "19:00 - 19:59"),
              (21, "20:00 - 20:59"),
              (22, "21:00 - 21:59"),
              (23, "22:00 - 22:59"),
              (0, "23:00 - 23:59"),
              )

# new pool form
class NewPoolForm(forms.Form):
    lat = forms.FloatField(label="Latitude", min_value=-90.0, max_value=90.0)
    long = forms.FloatField(label="Longitude", min_value=-180.0, max_value=180.0)
    date = forms.DateField(label="Date", initial=DT.date.today)
    # time = forms.TimeField(label="Time (GMT+0)", initial=DT.time(00, 00))
    hour = forms.ChoiceField(label="Time (GMT+0)", choices=TIME_SLOTS)
    odds = forms.FloatField(label="Decimal Odds", min_value=1.0)
    max_bet = forms.FloatField(label="Max Bet (US$)", min_value=20.0)

# add fund form
class AddFundForm(forms.Form):
    cc_number = CardNumberField(label='Card Number')
    cc_expiry = CardExpiryField(label='Expiration Date')
    cc_code = SecurityCodeField(label='CVV/CVC')
    fund = forms.FloatField(label="Amount (US$)", min_value=0.0)


# Create your views here.
def index(request):
    pools = Pool.objects.all()
    return renderIndex(request, pools, TIME_SLOTS)


def activeOnly(request):
    pools = Pool.objects.filter(active=True)
    return renderIndex(request, pools, TIME_SLOTS)


def search(request):
    keyword = request.GET.get('keyword')
    if keyword and keyword.strip() != "":
        keyword = keyword.lower()
        pools = Pool.objects.filter(keyword__contains=keyword)
        return renderIndex(request, pools, TIME_SLOTS)
    else:
        return HttpResponseRedirect(reverse('index'))
    


@login_required
def myPool(request):
    pools = Pool.objects.filter(house=request.user)
    return renderIndex(request, pools, TIME_SLOTS)


def odds(request):
    return render(request, "gambling/odds.html")


@login_required
def createPool(request):
    form = NewPoolForm()
    if request.method == "GET":
        return render(request, "gambling/newpool.html", {"form": form})
    else:
        form = NewPoolForm(request.POST)
        if request.user.balance < 0:
            messages.warning(request, "You can't open a pool with negative balance.")
            return render(request, "gambling/newpool.html", {"form": form})
        if form.is_valid():
            # for searching
            keyword = f"lat: {form.cleaned_data.get('lat')} long: {form.cleaned_data.get('long')} date: {form.cleaned_data.get('date')} house: {request.user}"
            
            # if mm > 0, hh += 1, but if the new hh is 24, then it becomes 0 and dd in date += 1
            # if form.cleaned_data.get('time').minute > 0:
            #     hour = form.cleaned_data.get('time').hour + 1
            #     if hour == 24:
            #         hour = 0
            #         date = form.cleaned_data.get('date') + DT.timedelta(days=1)    
            # else:
            #     hour = form.cleaned_data.get('time').hour
            #     date = form.cleaned_data.get('date')

            new_pool = Pool(house=request.user,
                            odds=form.cleaned_data.get('odds'),
                            lat=form.cleaned_data.get('lat'),
                            long=form.cleaned_data.get('long'),
                            date=form.cleaned_data.get('date'),
                            hour=form.cleaned_data.get('hour'),
                            max_bet=form.cleaned_data.get('max_bet'),
                            keyword=keyword.lower()
                            )
            new_pool.save()
            messages.success(request, "You created a new pool.")
            return HttpResponseRedirect(reverse("index"))
        else:
            messages.warning(request, "Please ensure the information is complete and valid.")
            return render(request, "gambling/newpool.html", {"form": form})
        

def validatePool(request):
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)
    
    # self-reminder: data is a dict, so data["..."] should be used
    data = json.loads(request.body)
    try:
        pool = Pool.objects.get(pk=int(data["pool_id"]))
    except:
        return JsonResponse({"error": "invalid pool id."}, status=400)
    else:
        # update the pool
        pool.winner = data["pool_winner"]
        pool.active = False
        pool.save()
        
        # update each relevant bet
        bets = Bet.objects.filter(pool=pool)
        if bets:
            # if the house wins, update the house's balance
            if pool.winner == "House":
                winnings = 0
                for bet in bets:
                    bet.win = False
                    bet.save()
                    winnings += bet.wager
                pool.house.balance += winnings
                pool.house.save()
            # if the punter wins, update the punter's balance, rounded DOWN to 2nd decimal place, and the house's
            else:
                losses = 0
                for bet in bets:
                    bet.win = True
                    bet.save()
                    payout = int(bet.wager * pool.odds * 100) / 100
                    bet.punter.balance += payout
                    bet.punter.save()
                    losses += payout
                pool.house.balance -= losses
                pool.house.save()

        # if the POST request contains a user_id, check the user's balance
        current_user = User.objects.get(pk=int(data["user_id"]))
        if current_user:
            message = current_user.balance
        else:
            message = None

        return JsonResponse({"message": message}, status=201)


def watchlist(request):
    if request.method == "GET":
        # only authenticated users can use GET to access watchlist
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("login"))
        else:
            # get the list of pools that the user is watching
            watchings = Following.objects.filter(user=request.user)
            
            # put all those watched pools inside pools
            pools = []
            if watchings:
                for watching in watchings:
                    pools.append(watching.pool)
            
            # same processing as index() from now on
            return renderIndex(request, pools, TIME_SLOTS)

    elif request.method == "POST":
        data = json.loads(request.body)
        try:
            user = User.objects.get(pk=int(data["user_id"]))
            pool = Pool.objects.get(pk=int(data["pool_id"]))
        except:
            return JsonResponse({"error": "invalid user/pool id."}, status=400)
        
        watchingRecord = Following.objects.filter(user=user, pool=pool)
        
        if watchingRecord:
            message = "unfollowed"
            watchingRecord.delete()
        else:
            message = "followed"
            new_following = Following(user=user, pool=pool)
            new_following.save()
        return JsonResponse({"message": message}, status=201)


@login_required
def profile(request):
    form = AddFundForm()
    bets = Bet.objects.filter(punter=request.user)
    pools = []
    if bets:
        for bet in bets:
            pools.append(bet.pool)
    
    pools = sortAndProcess(request, pools, TIME_SLOTS)

    return render(request, "gambling/profile.html", {
        "form": form,
        "pools": pools,
        })


@login_required
def addFund(request):
    if request.method != "POST":
        return HttpResponse("Bad request: invalid method")
    
    form = AddFundForm(request.POST)
    if form.is_valid():
        amount = form.cleaned_data.get("fund")
        request.user.balance += amount
        request.user.save()
        messages.success(request, f"${amount:.1f} added to your balance.")
    else:
        messages.warning(request, "Invalid Credit Card Information")
    return HttpResponseRedirect(reverse('profile'))

def wager(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    # self-reminder: data is a dict, so data["..."] should be used
    data = json.loads(request.body)
    try:
        punter = User.objects.get(pk=int(data["user_id"]))
        pool = Pool.objects.get(pk=int(data["pool_id"]))
    except:
        return JsonResponse({"error": "invalid data."}, status=400)
    else:
        # check if the punter is the pool's banker
        if pool.house == punter:
            return JsonResponse({"message": "Wager Rejected - no one can bet on their own pools."}, status=201)
        
        # check if the wager is valid, covered by user's balance, and within max_bet
        try:
            wager = int(data["wager"])
        except ValueError:
            message = "Wager Rejected - invalid wager amount."
            pass
        else:
            if wager > punter.balance:
                message = "Wager Rejected - insufficient fund."
            elif wager > pool.max_bet:
                message = "Wager Rejected - pool's max bet exceeded."
            else:
                # deduct the user's balance and create a new bet record
                punter.balance -= wager
                punter.save()
                new_bet = Bet(pool=pool, punter=punter, wager=wager)
                new_bet.save()

                message = f"Wager Accepted. New Balance:{punter.balance}"
        return JsonResponse({"message": message}, status=201)

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "gambling/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "gambling/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "gambling/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "gambling/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "gambling/register.html")
