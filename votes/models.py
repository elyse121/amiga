from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class Assignment(models.Model):
    """Weekly random vote target for a user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_from')
    hour_interval = models.DateTimeField(default=timezone.now)  # Keep same field name
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'hour_interval')

    def __str__(self):
        return f"{self.user.username} -> {self.assigned_to.username} ({self.hour_interval:%Y-%m-%W})"

class Vote(models.Model):
    """Auto-vote created from assignment."""
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes_cast')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes_received')
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name='vote')
    hour_interval = models.DateTimeField(default=timezone.now)  # Keep same field name
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('voter', 'hour_interval')

    def __str__(self):
        return f"{self.voter.username} votes for {self.recipient.username} ({self.hour_interval:%Y-%m-%W})"

class Rating(models.Model):
    """Rating given by user to someone who voted for them."""
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_received')
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE, related_name='ratings')
    score = models.IntegerField(choices=[(1, '1⭐'), (2, '2⭐'), (3, '3⭐'), (4, '4⭐'), (5, '5⭐')])
    rated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('rater', 'vote')

    def __str__(self):
        return f"{self.rater.username} rated {self.rated_user.username} {self.score}⭐"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_bestie = models.BooleanField(default=True)
    bio = models.CharField(max_length=200, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def average_rating(self):
        ratings = Rating.objects.filter(rated_user=self.user)
        if ratings.exists():
            return round(ratings.aggregate(models.Avg('score'))['score__avg'], 1)
        return 0

    @property
    def total_ratings(self):
        return Rating.objects.filter(rated_user=self.user).count()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()