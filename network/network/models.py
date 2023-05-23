from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Post(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.CharField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)

    def serialize(self):
        return {
            "id": self.id,
            "creator_id": self.creator.id,
            "timestamp": self.timestamp.strftime("%b %d %Y, %I:%M %p")
        }
    
    def __str__(self):
        return f"{self.creator.username} posted at {self.timestamp}"
    
class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} liked {self.post.id}"
    
class Following(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE)
    followed_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.follower.username} followed {self.followed_id}"
    