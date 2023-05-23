from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("new_listing", views.addListing, name="new"),
    path("listing/<int:listingID>", views.listing, name="listing"),
    path("watchlist", views.updateWatchlist, name="watchlist"),
    path("bid", views.bid, name="bid"),
    path("comment", views.postComment, name="comment"),
    path("close", views.closeListing, name="close"),
    path("category/<int:category>", views.getCategory, name="category"),
    path("categories", views.showCategory, name="categories")
]
