from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
import random
from datetime import timedelta
from .models import Assignment, Vote, Profile, Rating
from django.contrib.auth.models import User

def home(request):
    return redirect('/votes/')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'votes/registration/register.html', {'form': form})

@login_required
def index(request):
    user = request.user
    now = timezone.now()
    # Start of current week (Monday)
    current_week = now - timedelta(days=now.weekday())
    current_week = current_week.replace(hour=0, minute=0, second=0, microsecond=0)

    # Ensure ALL users have profiles
    all_users = User.objects.all()
    for user_obj in all_users:
        if not hasattr(user_obj, 'profile'):
            Profile.objects.create(user=user_obj)

    # Auto-create assignments for current week (using hour_interval field)
    if not Assignment.objects.filter(hour_interval=current_week, is_active=True).exists():
        users_list = list(all_users)
        
        if len(users_list) > 1:
            random.shuffle(users_list)
            for i, assigner in enumerate(users_list):
                assignee = users_list[(i + 1) % len(users_list)]
                if assignee != assigner:
                    assignment = Assignment.objects.create(
                        user=assigner,
                        assigned_to=assignee,
                        hour_interval=current_week,  # Use hour_interval field
                        is_active=True
                    )
                    Vote.objects.create(
                        voter=assigner,
                        recipient=assignee,
                        assignment=assignment,
                        hour_interval=current_week  # Use hour_interval field
                    )

    # Get ALL current assignments
    all_assignments = Assignment.objects.filter(hour_interval=current_week, is_active=True).select_related('user', 'assigned_to')
    
    # User's current assignment
    user_assignment = all_assignments.filter(user=user).first()

    # Check for unrated votes (people who voted for user in previous weeks)
    previous_votes = Vote.objects.filter(
        recipient=user,
        hour_interval__lt=current_week
    ).exclude(
        ratings__rater=user
    ).select_related('voter').order_by('-hour_interval')

    unrated_vote = previous_votes.first() if previous_votes.exists() else None

    # Calculate next week
    next_week = current_week + timedelta(days=7)
    time_remaining = next_week - now

    context = {
        'all_assignments': all_assignments,
        'user_assignment': user_assignment,
        'current_interval': current_week,
        'unrated_vote': unrated_vote,
        'days_remaining': int(time_remaining.total_seconds() // 86400),
        'hours_remaining': int((time_remaining.total_seconds() % 86400) // 3600),
        'next_week': next_week.strftime('%Y-%m-%d'),
        'user': user,
    }
    return render(request, 'votes/index.html', context)

@login_required
def submit_rating(request):
    if request.method == 'POST':
        vote_id = request.POST.get('vote_id')
        score = request.POST.get('score')
        
        try:
            vote = Vote.objects.get(id=vote_id)
            if vote.recipient != request.user:
                return JsonResponse({'error': 'Invalid rating'}, status=400)
            
            rating, created = Rating.objects.get_or_create(
                rater=request.user,
                vote=vote,
                defaults={'rated_user': vote.voter, 'score': score}
            )
            
            if not created:
                rating.score = score
                rating.save()
            
            return JsonResponse({'success': True, 'message': 'Rating submitted!'})
            
        except Vote.DoesNotExist:
            return JsonResponse({'error': 'Vote not found'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_assignments(request):
    now = timezone.now()
    current_week = now - timedelta(days=now.weekday())
    current_week = current_week.replace(hour=0, minute=0, second=0, microsecond=0)

    all_assignments = Assignment.objects.filter(hour_interval=current_week, is_active=True).select_related('user', 'assigned_to')
    
    assignments_list = [{'assigner': a.user.username, 'assignee': a.assigned_to.username} for a in all_assignments]

    next_week = current_week + timedelta(days=7)
    time_remaining = next_week - now

    return JsonResponse({
        'assignments': assignments_list,
        'interval': current_week.strftime('%Y-%m-%d'),
        'days_remaining': int(time_remaining.total_seconds() // 86400),
        'hours_remaining': int((time_remaining.total_seconds() % 86400) // 3600)
    })