
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("post", views.post, name="post"),
    path("profile/<str:user_id>", views.profile, name="profile"),
    path("following", views.following, name="following"),
    path("edit", views.editPost, name="edit"),
    path("edit/<int:post_id>", views.getPost, name="fetch_edit"),
    path("like", views.likePost, name="like"),
    path("follow", views.follow, name="follow"),
]
