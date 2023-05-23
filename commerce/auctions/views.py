from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django import forms
from django.utils.dateparse import parse_date
from django.contrib import messages
from .helpers import sortBids, countWatchlist
import datetime

from .models import User, Listing, Bid, Comment, Watchlist

CATEGORIES = ["Undefined", "Monster", "Help", "SP", "Help/SP", "R", "Ch", "Summoner", "F", "Astrology"]

class NewListingForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs={'name':'title', 'id':'title'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'name':'description', 'id':'description'}))
    starting_bid = forms.IntegerField(widget=forms.NumberInput(attrs={'name':'starting_bid', 'id':'starting_bid'}))
    picture = forms.URLField(required=False, widget=forms.URLInput(attrs={'name':'picture', 'id':'picture'}))
    CHOICES = ((CATEGORIES[0], "---"), (CATEGORIES[1], CATEGORIES[1]), (CATEGORIES[2], CATEGORIES[2]), (CATEGORIES[3], CATEGORIES[3]), (CATEGORIES[4], CATEGORIES[4]), (CATEGORIES[5], CATEGORIES[5]), (CATEGORIES[6], CATEGORIES[6]), (CATEGORIES[7], CATEGORIES[7]), (CATEGORIES[8], CATEGORIES[8]), (CATEGORIES[9], CATEGORIES[9]))
    category = forms.CharField(label='Category', widget=forms.Select(choices=CHOICES))
    # expiry = forms.DateTimeField(widget=forms.DateInput(attrs={'name':'expiry', 'id':'expiry'}))


def index(request):
    listings = Listing.objects.filter(open=True)
        
    return render(request, "auctions/index.html", {
        "header": "Active Listing",
        "listings": sortBids(listings),
        "watchedNum": countWatchlist(request)
    })


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
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure username and email are not empty
        if username == None or username.strip() == "" or email == None or email.strip() == "":
            return render(request, "auctions/register.html", {
                "message": "Username and email can't be empty."
            })
        
        # Ensure password contains at least 4 characters and matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password == None or len(password.strip()) < 4 or password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match and contain at least 4 characters."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def addListing(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    else:
        if request.method == "GET":
            return render(request, "auctions/new_listing.html", {
                "form": NewListingForm,
                "watchedNum": countWatchlist(request)
            })
        else:
            title = request.POST.get("title")
            desc = request.POST.get("description")
            starting_bid = request.POST.get("starting_bid")
            # expiry = request.POST.get("expiry")
            # check if any of the three fields above are empty or invalid
            if title is not None and title.strip() != "" and desc is not None and desc.strip() != "" and starting_bid is not None and starting_bid != "":
                
                # try to parse expiry date
                # try:
                #     expiry = parse_date(expiry)
                # except ValueError:
                #     return render(request, "auctions/new_listing.html", {
                #         "form": NewListingForm,
                #         "message": "Expiry Date Format: YYYY-MM-DD"
                #         })
                
                # try to convert starting_bid into an integer for checking if it is greater than zero
                try:
                    starting_bid = int(starting_bid)
                except:
                    return render(request, "auctions/new_listing.html", {
                        "form": NewListingForm,
                        "message": "Invalid Starting Bid"
                        })
                if starting_bid <= 0:
                    return render(request, "auctions/new_listing.html", {
                        "form": NewListingForm,
                        "message": "Starting bid must be greater than zero"
                        })

                # by this point, the new listing is valid and can be accepted
                else:
                    new_listing = Listing(title = title, 
                                          desc = desc, 
                                          starting_bid = starting_bid,
                                          pic = request.POST.get("picture"), 
                                          category = request.POST.get("category"), 
                                        #   expiry = expiry, 
                                          bidder = request.user)
                    new_listing.save()
                    # to be updated later
                    return HttpResponseRedirect(reverse("index"))

            else:
                return render(request, "auctions/new_listing.html", {
                        "form": NewListingForm,
                        "message": "Title, description and starting bid must be filled in.",
                        "watchedNum": countWatchlist(request)
                        })


def listing(request, listingID):
    # try to get listing and its creator's id
    try:
        item = Listing.objects.get(pk=listingID)
        creator = User.objects.get(pk=int(item.bidder.id))
    except item.DoesNotExist:
        return HttpResponse("Bad request: listing doesn't exist")
    except creator.DoesNotExist:
        return HttpResponse("Bad request: creator of the listing doesn't exist")
    
    # the following parameters are only applicable to authenticated users
    if request.user.is_authenticated:
        # check if the user has included the listing in their watchlist
        watcheditems = Watchlist.objects.filter(listing=item, bidder=request.user)
        if watcheditems:
            watched = True
        else:
            watched = None
        print(f"creator: {creator} and user.id: {request.user.id}")
        
        # check if the user is also creator of the listing
        if request.user.id == creator.id:
            createdByUser = True
        else:
            createdByUser = None
        
        # check if user is the winner
        if request.user.id == item.winner_id:
            wonByUser = True
        else:
            wonByUser = None
    else:
        watched = None
        createdByUser = None
        wonByUser = None

    # retrieve the highest bid
    def Fn(dict):
        return -int(dict.bid)
    
    bids = Bid.objects.filter(listing=item)
    if bids:
        bids = sorted(bids, key=Fn)
        item.price = int(bids[0].bid)
        item.bidQty = len(bids)
    else:
        item.price = 0
        item.bidQty = 0
    
    # retrieve all relevant comments
    comments = Comment.objects.filter(listing=item)

    return render(request, "auctions/listing.html", {
        "item": item,
        "creator": creator,
        "watched": watched,
        "createdByUser": createdByUser,
        "wonByUser": wonByUser,
        "comments": comments,
        "watchedNum": countWatchlist(request)
    })


def updateWatchlist(request):
    # only authenticated user can use the watchlist-related functions
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    else:
        # render watchlist page (i.e., index.html) if it's a GET request
        if request.method == "GET":
            watcheditems = Watchlist.objects.filter(bidder=request.user)
            listings = []
            for item in watcheditems:
                listings.append(Listing.objects.get(pk=item.listing.id))
            # print("watcheditems: ", watcheditems)
            # print("listings: ", listings)
            # return render(request, "auctions/watchlist.html", {
            #     "bidder": request.user,
            #     "listings": listings
            #     })
            return render(request, "auctions/index.html", {
                    "header": request.user.username + "'s Watchlist",
                    "listings": sortBids(listings),
                    "watchedNum": countWatchlist(request)
                })
        # for POST request...
        else:
            try:
                listing = Listing.objects.get(pk=request.POST.get("listing_id"))
            except:
                return HttpResponse("Bad request: listing doesn't exist")
            watcheditem = Watchlist.objects.filter(bidder=request.user, listing=listing)
            # remove the item from watchlist if it already exists
            print("listing: ", listing)
            if watcheditem:
                watcheditem.delete()
            # create a new item in watchlist if it doesn't exist 
            else:
                new_watcheditem = Watchlist(bidder=request.user, listing=listing)
                new_watcheditem.save()
            messages.success(request, "Watchlist Updated")
            return HttpResponseRedirect(reverse("listing", args=(listing.id,)))


def bid(request):
    if request.method == "POST":
        # try to convert user's inputs into integers
        try:
            new_bid = int(request.POST.get("new_bid"))
            listing_id = int(request.POST.get("listing_id"))
        except:
            return HttpResponse("Bad request: invalid bid")
        
        listing = Listing.objects.get(pk=listing_id)
        # another validation, in case the user feeds an invalid listing_id
        try:
            starting_bid = int(listing.starting_bid)
        except:
            return HttpResponse("Bad request: the listing doesn't exist")
        
        # retrieve the highest bid
        def Fn(dict):
            return -int(dict.bid)
        
        bids = Bid.objects.filter(listing=listing)
        if bids:
            bids = sorted(bids, key=Fn)
            price = int(bids[0].bid)
        else:
            price = 0
 
        if new_bid > price and new_bid >= starting_bid:
            newBid = Bid(bidder=request.user, listing=listing, bid=new_bid)
            newBid.save()
            messages.success(request, f"You submitted a bid of ${new_bid}")
        else:
            messages.warning(request, "The bid is too low.")
        
        return HttpResponseRedirect(reverse("listing", args=(listing.id,)))


def closeListing(request):
    if request.method == "POST":
        # close the bid
        try:
            listing_id = int(request.POST.get("listing_id"))
        except:
            return HttpResponse("Bad request: listing doesn't exist")
        listing = Listing.objects.get(pk=listing_id)
        listing.open = False
        # check if the bid has a winner and update the listing's record
        bids = Bid.objects.filter(listing=listing)
        if bids:
            def Fn(dict):
                return -int(dict.bid)
                
            bids = sorted(bids, key=Fn)
            listing.winner_id = bids[0].bidder.id
        # save the updates made to listing
        listing.save()    
        return HttpResponseRedirect(reverse("listing", args=(listing.id,)))


def postComment(request):
    if request.method == "POST":
        comment = request.POST.get("comment")
        listing_id = int(request.POST.get("listing_id"))
        listing = Listing.objects.get(pk=listing_id)
        # post_time = datetime.datetime.now()
        new_comment = Comment(listing=listing, bidder=request.user, comment=comment)
        new_comment.save()
        return HttpResponseRedirect(reverse("listing", args=(listing.id,)))
    

def getCategory(request, category):
    try:
        category = CATEGORIES[category]
    except:
        return HttpResponse("Bad request: invalid category")
    listings = Listing.objects.filter(category=category)
    return render(request, "auctions/index.html", {
        "header": "Category:" + category,
        "listings": sortBids(listings),
        "watchedNum": countWatchlist(request)
    })


def showCategory(request):
    categories = []
    for i in range(len(CATEGORIES)):
        categories.append({"num": i, "title": CATEGORIES[i]})
    return render(request, "auctions/categories.html", {
        "categories": categories,
        "watchedNum": countWatchlist(request)
    })