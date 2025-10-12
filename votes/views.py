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
    
    # Calculate start of current weekly period (Saturday at 20:00)
    delta_days = (now.weekday() - 5) % 7  # 5 = Saturday
    last_saturday = now - timedelta(days=delta_days)
    last_sat_20 = last_saturday.replace(hour=20, minute=0, second=0, microsecond=0)
    
    if now < last_sat_20:
        current_interval = last_sat_20 - timedelta(days=7)
    else:
        current_interval = last_sat_20

    # Ensure ALL users have profiles
    all_users = User.objects.all()
    for user_obj in all_users:
        if not hasattr(user_obj, 'profile'):
            Profile.objects.create(user=user_obj)

    # Check if ALL users have assignments for current weekly interval
    users_with_assignments = Assignment.objects.filter(
        hour_interval=current_interval, 
        is_active=True
    ).values_list('user_id', flat=True)
    
    users_without_assignments = all_users.exclude(id__in=users_with_assignments)
    
    # If ANY user is missing assignment, recreate ALL assignments for the interval
    if users_without_assignments.exists() or Assignment.objects.filter(hour_interval=current_interval).count() != all_users.count():
        # Delete existing assignments for this interval
        Assignment.objects.filter(hour_interval=current_interval).delete()
        Vote.objects.filter(hour_interval=current_interval).delete()
        
        # Create new assignments for ALL users
        users_list = list(all_users)
        import random
        random.shuffle(users_list)
        
        if len(users_list) > 1:
            # Create a circular assignment (user1->user2, user2->user3, ..., last->user1)
            for i, assigner in enumerate(users_list):
                assignee = users_list[(i + 1) % len(users_list)]
                
                # Create assignment
                assignment = Assignment.objects.create(
                    user=assigner,
                    assigned_to=assignee,
                    hour_interval=current_interval,
                    is_active=True
                )
                
                # Create corresponding vote
                Vote.objects.create(
                    voter=assigner,
                    recipient=assignee,
                    assignment=assignment,
                    hour_interval=current_interval
                )
        elif len(users_list) == 1:
            # Only one user - assign to themselves
            single_user = users_list[0]
            assignment = Assignment.objects.create(
                user=single_user,
                assigned_to=single_user,
                hour_interval=current_interval,
                is_active=True
            )
            Vote.objects.create(
                voter=single_user,
                recipient=single_user,
                assignment=assignment,
                hour_interval=current_interval
            )

    # Get ALL current assignments
    all_assignments = Assignment.objects.filter(hour_interval=current_interval, is_active=True).select_related('user', 'assigned_to')
    
    # User's current assignment
    user_assignment = all_assignments.filter(user=user).first()

    # Check for unrated votes (people who voted for user in previous intervals)
    previous_votes = Vote.objects.filter(
        recipient=user,
        hour_interval__lt=current_interval
    ).exclude(
        ratings__rater=user
    ).select_related('voter').order_by('-hour_interval')

    unrated_vote = previous_votes.first() if previous_votes.exists() else None

    # Calculate next weekly interval (next Saturday 20:00)
    next_interval = current_interval + timedelta(days=7)
    time_remaining = next_interval - now
    
    # Calculate countdown components
    total_seconds = int(time_remaining.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    context = {
        'all_assignments': all_assignments,
        'user_assignment': user_assignment,
        'current_interval': current_interval,
        'unrated_vote': unrated_vote,
        'days_remaining': days,
        'hours_remaining': hours,
        'minutes_remaining': minutes,
        'seconds_remaining': seconds,
        'next_interval': next_interval.strftime('%Y-%m-%d'),
        'user': user,
        'total_users': all_users.count(),
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
@login_required
def refresh_assignments(request):
    if request.method == 'POST' and request.user.is_superuser:
        result = recreate_weekly_assignments()
        messages.success(request, result)
    else:
        messages.error(request, "Only admin can refresh assignments")
    return redirect('index')
def recreate_weekly_assignments():
    """Recreate assignments for all users for current week"""
    now = timezone.now()
    current_week = now - timedelta(days=now.weekday())
    current_week = current_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    all_users = list(User.objects.all())
    
    # Delete existing assignments for this week
    Assignment.objects.filter(hour_interval=current_week).delete()
    Vote.objects.filter(hour_interval=current_week).delete()
    
    if len(all_users) < 2:
        return "Need at least 2 users for assignments"
    
    # Create circular assignments
    random.shuffle(all_users)
    
    for i, assigner in enumerate(all_users):
        assignee = all_users[(i + 1) % len(all_users)]
        
        assignment = Assignment.objects.create(
            user=assigner,
            assigned_to=assignee,
            hour_interval=current_week,
            is_active=True
        )
        
        Vote.objects.create(
            voter=assigner,
            recipient=assignee,
            assignment=assignment,
            hour_interval=current_week
        )
    
    return f"Created assignments for {len(all_users)} users"

# Add this to your register view to auto-refresh when new users join
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            # Auto-refresh assignments when new user registers
            if User.objects.count() > 1:
                recreate_weekly_assignments()
            
            messages.success(request, f'Account created for {username}! Assignments updated!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'votes/registration/register.html', {'form': form})