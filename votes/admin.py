from django.contrib import admin
from .models import Profile, Assignment, Vote, Rating

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_bestie', 'average_rating', 'total_ratings', 'date_joined')
    list_filter = ('is_bestie', 'date_joined')
    search_fields = ('user__username', 'bio')
    readonly_fields = ('average_rating', 'total_ratings')

    def average_rating(self, obj):
        return obj.average_rating
    average_rating.short_description = 'Avg Rating'

    def total_ratings(self, obj):
        return obj.total_ratings
    total_ratings.short_description = 'Total Ratings'

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'assigned_to', 'hour_interval', 'is_active')
    list_filter = ('hour_interval', 'is_active')
    search_fields = ('user__username', 'assigned_to__username')

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'recipient', 'hour_interval', 'timestamp')
    list_filter = ('hour_interval', 'timestamp')
    search_fields = ('voter__username', 'recipient__username')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('rater', 'rated_user', 'score', 'vote', 'rated_at')
    list_filter = ('score', 'rated_at')
    search_fields = ('rater__username', 'rated_user__username')