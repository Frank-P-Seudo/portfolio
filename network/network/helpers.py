from .models import User, Post, Like, Following

def sortAndCount(request, posts):
  # sort the posts by timestamp, in reverse chronlogical order
  def Fn(item):
    timestamp = item.timestamp
    return -int(timestamp.strftime("%Y%m%d%H%M%S"))
  
  posts = sorted(posts, key=Fn)

  for post in posts:
    # compute like count for each post
    likes = Like.objects.filter(post=post)
    if likes:
      post.like_count = likes.count()
    else:
      post.like_count = 0
    
    # additional checking for authenticated user...
    if request.user.is_authenticated:
      
      # check if the post was created by current user
      if post.creator == request.user:
        post.createdByUser = True
      
      # check if the post was liked by the user already
      likeRecord = Like.objects.filter(post=post, user=request.user)
      if likeRecord:
        post.liked = True
      else:
        post.liked = None
          
  return posts