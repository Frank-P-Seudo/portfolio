from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("odds", views.odds, name="odds"),
    path("newpool", views.createPool, name="new"),
    path("validate", views.validatePool, name="validate"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("profile", views.profile, name="profile"),
    path("fund", views.addFund, name="fund"),
    path("wager", views.wager, name="wager"),
    path("activepool", views.activeOnly, name="active"),
    path("mypools", views.myPool, name="myPool"),
    path("search", views.search, name="search"),
]