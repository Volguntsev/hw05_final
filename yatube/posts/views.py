from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
# from django.views.decorators.cache import cache_page

from .settings import COUNT_POSTS_IN_PAGE
from .forms import CommentForm, PostForm
from .models import Follow, Post, Group, User


def get_page_obj(request, posts):
    paginator = Paginator(posts, COUNT_POSTS_IN_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


# @cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    page_obj = get_page_obj(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = get_page_obj(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = get_page_obj(request, posts)
    if request.user.is_anonymous:
        context = {
            'author': author,
            'page_obj': page_obj,
        }
        return render(request, template, context)

    else:
        following = Follow.objects.filter(
            user=request.user,
            author=User.objects.get(username=username)
        ).exists()
        context = {
            'author': author,
            'page_obj': page_obj,
            'following': following
        }
        return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(
        request.POST or None)
    context = {
        'post': post,
        'comments': post.comments.all,
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, template, {'form': form}, )

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
    template = 'posts/create_post.html'
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    context = {
        'form': form,
        'is_edit': True,
        'post_id': post_id,
    }
    return render(request, template, context)


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
    template = 'posts/follow.html'
    posts = Post.objects.filter(
        author__following__user=request.user
    )
    page_obj = get_page_obj(request, posts)
    context = {
        'page_obj': page_obj,
        'author': request.user
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    if ((username != request.user.username) and (not Follow.objects.filter(
            user=request.user,
            author=User.objects.get(username=username))).exists()):
        Follow.objects.create(
            user=request.user,
            author=get_object_or_404(User, username=username))
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user,
        author=User.objects.get(username=username)).delete()
    return redirect('posts:profile', username=username)
