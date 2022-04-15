from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import NUMBER_OF_POSTS_PER_PAGE

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


User = get_user_model()


def method_paginator(queriset, request):
    paginator = Paginator(queriset, NUMBER_OF_POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj
    }


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    context = method_paginator(posts, request)
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'posts': posts,
    }
    context.update(method_paginator(posts, request))
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.author_posts.all()
    count = posts.count()
    following = request.user.is_authenticated and author.following.exists()
    context = {
        'author': author,
        'posts': posts,
        'count': count,
        'following': following,
    }
    context.update(method_paginator(posts, request))
    return render(request, template, context)


def post_detail(request, post_id):
    form = CommentForm(
        request.POST or None,
        files=request.FILES or None
    )
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    count = post.author.author_posts.count()
    comments = post.comments.filter(active=True)
    context = {
        'post': post,
        'count': count,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not post.author == request.user:
        return redirect('posts:profile', request.user.username)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    return render(
        request,
        'posts/create_post.html',
        {'form': form, 'post': post, 'is_edit': 'is_edit'}
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts =  Post.objects.filter(
        author__following__user=request.user
    )
    context = {
        'posts': posts,
    }
    context.update(method_paginator(posts, request))
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', request.user.username)
    follower = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    if follower is True:
        return redirect('posts:profile', request.user.username)
    Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', request.user.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', request.user.username)
    following = get_object_or_404(Follow, user=request.user, author=author)
    following.delete()
    return redirect('posts:profile', request.user.username)
