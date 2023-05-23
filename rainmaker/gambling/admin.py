from django.contrib import admin
from .models import User, Pool, Bet, Following

# Register your models here.
admin.site.register(User)
admin.site.register(Pool)
admin.site.register(Bet)
admin.site.register(Following)
