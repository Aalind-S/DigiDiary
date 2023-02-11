from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile, Post, LikePost, FollowersCount
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from itertools import chain
import random
# Create your views here.

# model.objects.filter returns a queryset 
# models.object.get returns the model object/instance

@login_required(login_url='signin')
def index(request):
    user_obj = User.objects.get(username = request.user.username)
    user_profile = Profile.objects.get(user=user_obj)
    #feed_post = Post.objects.all()
    feed = []
    user_following_list = []
    user_following = FollowersCount.objects.filter(follower=user_obj.username)
    for usr in user_following:
        user_following_list.append(usr.user) # why user? bcz followercount model stores username as user
    
    for usrname in user_following_list:
        feed_lists = Post.objects.filter(user=usrname)
        feed.append(feed_lists)
    
    feed_list = list(chain(*feed))


    # user suggestions
    all_users = User.objects.all()
    user_following_all = []

    for user in user_following:
        user_list = User.objects.get(username=user.user)
        user_following_all.append(user_list)
    
    new_suggestions_list = [x for x in list(all_users) if (x not in list(user_following_all))]
    current_user = User.objects.filter(username=request.user.username)
    final_suggestions_list = [x for x in list(new_suggestions_list) if ( x not in list(current_user))]
    random.shuffle(final_suggestions_list)

    username_profile = []
    username_profile_list = []

    for users in final_suggestions_list:
        username_profile.append(users.id)

    for ids in username_profile:
        profile_lists = Profile.objects.filter(id_user=ids)
        username_profile_list.append(profile_lists)

    suggestions_username_profile_list = list(chain(*username_profile_list))


    return render(request, 'index.html', {'user_profile': user_profile, 'feed_post':feed_list, 'suggestions_username_profile_list': suggestions_username_profile_list[:4]})




@login_required(login_url='signin')
def settings(request):
    return render(request, 'setting.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:

            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email is already taken')
                return redirect('signup')

            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username is already taken')
                return redirect('signup')

            else:

                user = User.objects.create_user(username=username, email = email, password = password)
                user.save()
                
                # log the user and open settings ig  
                user_profile = authenticate(username = username, password = password)
                login(request, user_profile)

                # now we assign a profile to the user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user = user_model.id)
                new_profile.save()
                return redirect('settings')
        else:   
            messages.info(request, 'Password does not match')
            return redirect('signup')
    else:
        return render(request, 'signup.html')
    
def signin(request):

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username= username, password = password)
        if user:
            login(request, user)
            return redirect('/')    
        else:
            pass
    return render(request, 'signin.html')

#@login_required
def logout(request):
    if request.user.is_authenticated:
        auth_logout(request)
        return redirect('signin')

@login_required
def settings(request):
    user_profile = Profile.objects.get(user = request.user)
    if request.method == "POST":

        if request.FILES.get('image') is None:
            image = user_profile.profileimg

        elif request.FILES.get('image'):
            image = request.FILES.get('image')
        
        bio = request.POST['bio']
        location = request.POST['location']

        user_profile.profileimg = image
        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()
        
    return render(request, 'setting.html', {'user_profile': user_profile})

@login_required
def upload(request):

    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']

        new_post = Post.objects.create(user=user, image = image, caption=caption)
        new_post.save()

        return redirect('/')
    else:
        return redirect('/')

@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id=post_id)
    like_flag = LikePost.objects.filter(post_id=post_id, username=username).first()
    
    if not like_flag:
        # post is not liked since like_flag is null or empty
        new_like = LikePost.objects.create(post_id=post_id, username = username)
        new_like.save()
        post.no_of_likes += 1

    else:
        # post is already liked so delete the like
        like_flag.delete()
        post.no_of_likes -= 1

    post.save()
    return redirect('/')

@login_required(login_url='signin')
def profile(request, pk):
    user_obj = User.objects.get(username = pk)
    user_profile = Profile.objects.get(user=user_obj)
    user_posts = Post.objects.filter(user=pk)
    user_post_len = len(user_posts)

    follower = request.user.username
    user = pk
    follow_flag = FollowersCount.objects.filter(follower=follower, user=user).first()

    if follow_flag:
        # already follows the user so unfollow
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    #calculating followers
    user_followers = len(FollowersCount.objects.filter(user=pk))
    #calculating the following
    user_following = len(FollowersCount.objects.filter(follower=pk))
    context = {
        'user_obj':user_obj,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_len':user_post_len,
        'button_text':button_text,
        'user_followers':user_followers,
        'user_following':user_following
    }
    return render(request, 'profile.html', context)

@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']
        follow_flag = FollowersCount.objects.filter(follower=follower, user = user).first()

        if follow_flag:
            # already following so unfollow
            del_follower = FollowersCount.objects.get(follower=follower, user = user)
            del_follower.delete()

            return redirect('/profile/'+user)
    
        else:
            # not followed yet so add the follower and save it
            new_follower = FollowersCount.objects.create(follower=follower, user = user)
            new_follower.save()

            return redirect('/profile/'+user)
    else:
        return redirect('/')
  
@login_required(login_url='signin')
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == 'POST':
        username = request.POST['username']
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []
        username_profile_list = []

        for users in username_object:
            username_profile.append(users.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)
        
        username_profile_list = list(chain(*username_profile_list))
    return render(request, 'search.html', {'user_profile': user_profile, 'username_profile_list': username_profile_list})