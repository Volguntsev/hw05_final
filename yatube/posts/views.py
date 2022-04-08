from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Post, Group, User
from .settings import COUNT_POSTS_IN_PAGE


def get_page_obj(request, posts):
    return Paginator(
        posts, COUNT_POSTS_IN_PAGE).get_page(
            request.GET.get('page'))


# @cache_page(20, key_prefix='index_page')
def index(request):
    return render(
        request,
        'posts/index.html',
        {'page_obj': get_page_obj(request, Post.objects.all())})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    context = {
        'group': group,
        'page_obj': get_page_obj(request, group.posts.all()),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = (
        (request.user.is_authenticated) and (
            request.user.username != username) and (
                Follow.objects.filter(
                    user=request.user,
                    author=author).exists()
        )
    )
    context = {
        'author': author,
        'page_obj': get_page_obj(request, author.posts.all()),
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    context = {
        'post': get_object_or_404(Post, pk=post_id),
        'form': CommentForm(request.POST or None),
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form}, )

    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    context = {
        'form': form,
        'is_edit': True,
        'post_id': post_id,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    context = {
        'page_obj': get_page_obj(
            request, Post.objects.filter(
                author__following__user=request.user)),
        'author': request.user
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if ((username != request.user.username) and (not Follow.objects.filter(
            user=request.user,
            author=author).exists())):
        Follow.objects.create(
            user=request.user,
            author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user,
        author__username=username).delete()
    return redirect('posts:profile', username=username)
