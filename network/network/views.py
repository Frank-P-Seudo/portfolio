from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from .helpers import sortAndCount
import datetime
from django.core.paginator import Paginator
from django.views.generic import ListView
from django.http import JsonResponse
import json

from .models import User, Post, Like, Following

def index(request):
    posts = Post.objects.all()
    # sort and add additional fields to posts, via a helper func
    posts = sortAndCount(request, posts)
    # pagination stuff
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    if page_number is None:
        page_number = 1
    posts = paginator.get_page(page_number)

    
    return render(request, "network/index.html", {
        "posts": posts,
        "index": True,
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
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


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
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


def post(request):
    # ensure the user is authenticated
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    else:
        # ensure the method is POST
        if request.method == "POST":
            post = request.POST.get("post")
            # ensure the post is not blank
            if post is not None and post.strip() != "":
                # save the post
                new_post = Post(creator=request.user,
                                post=post,
                                timestamp=datetime.datetime.now())
                new_post.save()
            else:
                # provide flash message when the post is empty
                messages.warning("Please ensure the post is not blank.")
            return HttpResponseRedirect(reverse("index"))
        else:
            return HttpResponse("Bad request: only POST method is allowed.")
        

def profile(request, user_id):
    # victim as in 'victim of stalking' and/or 'victim of cyberbullying'
    try:
        victim = User.objects.get(pk=user_id)
    except:
        return HttpResponse("Bad request: the user doesn't exist.")
    # get all posts of victim and process them with sortAndCount
    posts = Post.objects.filter(creator=victim)
    if posts:
        posts = sortAndCount(request, posts)

    # pagination stuff
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    if page_number is None:
        page_number = 1
    posts = paginator.get_page(page_number)
    
    # count the number of users stalking the victim, and let victim carry the count
    followers = Following.objects.filter(followed_id=victim.id)
    if followers:
        victim.follower_count = followers.count()
    else:
        victim.follower_count = 0

    # count the number of users whom the victim follows, and let victim carry the count
    followings = Following.objects.filter(follower=victim)
    if followings:
        victim.following_count = followings.count()
    else:
        victim.following_count = 0

    # check if the user is viewing their own profile, and let victim carry the bool value
    if victim == request.user:
        victim.narcissistic = True

    # if the victim isn't the user AND isn't already followed by the user, then let victim carry another bool value
    if request.user.is_authenticated:
        if victim != request.user:
            followingRecord = Following.objects.filter(follower=request.user, followed_id=victim.id)
            if followingRecord:
                victim.followed = True

    return render(request, "network/index.html", {
        "victim": victim,
        "posts": posts,
    })


def following(request):
    # ensure the user is authenticated
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    else:
        # get the list of users that the user is following
        followings = Following.objects.filter(follower=request.user)
        
        # put all those followed users' posts inside a list
        posts = []
        if followings:
            for following in followings:
                follower = User.objects.get(pk=int(following.followed_id))
                f_posts = Post.objects.filter(creator=follower)
                print(f'posts by id {following.followed_id}: {f_posts}')
                if f_posts:
                    posts.extend(f_posts)

        # if posts isn't empty, process it with sortAndCount()
        if posts:
            posts = sortAndCount(request, posts)
        
        # pagination stuff
        paginator = Paginator(posts, 10)
        page_number = request.GET.get('page')
        if page_number is None:
            page_number = 1
        posts = paginator.get_page(page_number)

        return render(request, "network/index.html", {
            "posts": posts
        })


def getPost(request, post_id):
    post = Post.objects.filter(pk=int(post_id))
    if post:
        message = post[0].post    
    else:
        message = "Friendly reminder - make your post less cringey"
    return JsonResponse({"message": message}, status=201)


def editPost(request):
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)
    
    # self-reminder: data is a dict, so data["..."] should be used
    data = json.loads(request.body)
    try:
        post = Post.objects.get(pk=int(data["post_id"]))
    except:
        return JsonResponse({"error": "invalid post id."}, status=400)
    
    edited_post = data["post"]
    if edited_post and edited_post.strip() != "":
        post.post = edited_post
    else:
        post.post = "deleted"
    post.save()
    return HttpResponse(status=204)



def likePost(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    # self-reminder: data is a dict, so data["..."] should be used
    data = json.loads(request.body)
    try:
        post = Post.objects.get(pk=int(data["post_id"]))
        user = User.objects.get(pk=int(data["user_id"]))
    except:
        return JsonResponse({"error": "invalid post/user id."}, status=400)
    
    likeRecord = Like.objects.filter(post=post, user=user)
    if likeRecord:
        # if like record exists, delete it and tell JS it's unliked
        likeRecord.delete()
        message = "unliked"
        
    else:
        # otherwise, save a new like record and tell JS it's liked
        new_like = Like(post=post, 
                        user=user, 
                        timestamp=datetime.datetime.now()
                        )
        new_like.save()
        message = "liked"
    return JsonResponse({"message": message}, status=201)


def follow(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    # self-reminder: data is a dict, so data["..."] should be used
    data = json.loads(request.body)
    try:
        user = User.objects.get(pk=int(data["user_id"]))
        victim = User.objects.get(pk=int(data["victim_id"]))
    except:
        return JsonResponse({"error": "invalid user/victim id."}, status=400)
    
    followingRecord = Following.objects.filter(follower=user, followed_id=victim.id)
    
    if followingRecord:
        message = "unfollowed"
        followingRecord.delete()
    else:
        message = "followed"
        new_following = Following(follower=user, followed_id=victim.id)
        new_following.save()
    return JsonResponse({"message": message}, status=201)