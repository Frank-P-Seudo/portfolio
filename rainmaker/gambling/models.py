from django.db import models
from django.contrib.auth.models import AbstractUser
import datetime

# Create your models here.
class User(AbstractUser):
    balance = models.FloatField(default=0)
    pass

WINNERS = (("House", "House"), ("Punter", "Punter"))

# keyword is allowed to be blank to facilitate demo
class Pool(models.Model):
    house = models.ForeignKey(User, on_delete=models.CASCADE)
    odds = models.FloatField()
    long = models.FloatField()
    lat = models.FloatField()
    date = models.DateField()
    hour = models.IntegerField()
    max_bet = models.FloatField()
    active = models.BooleanField(default=True)
    winner = models.CharField(max_length=6, choices=WINNERS, null=True, blank=True)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    keyword = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"Long {self.long}, Latitude {self.lat} at {self.date}"


class Bet(models.Model):
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE)
    punter = models.ForeignKey(User, on_delete=models.CASCADE)
    wager = models.FloatField()
    win = models.BooleanField(null=True, blank=True)
    timestamp = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return f"{self.punter} bets {self.wager} on {self.pool}"


class Following(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} follows {self.pool}"