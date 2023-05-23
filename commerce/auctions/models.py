from django.contrib.auth.models import AbstractUser
from django.db import models
import datetime

class User(AbstractUser):
    pass

class Listing(models.Model):
    title = models.CharField(max_length=64)
    desc = models.CharField(max_length=200)
    starting_bid = models.IntegerField()
    pic = models.URLField(max_length=400, null=True, blank=True)
    category = models.CharField(max_length=64, null=True, blank=True)
    open = models.BooleanField(default=True)
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    winner_id = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} starting at ${self.starting_bid}"

class Bid(models.Model):
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    bid = models.IntegerField()

    def __str__(self):
        return f"{self.bidder.username}: ${self.bid} for {self.listing.title}"
    
class Comment(models.Model):
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    comment = models.CharField(max_length=200)
    post_time = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return f"{self.bidder} bidding for {self.listing}"

class Watchlist(models.Model):
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.bidder} watching {self.listing}"
