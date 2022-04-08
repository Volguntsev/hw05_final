import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .const import SMALL_GIF
from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, User, Comment

GROUP_SLUG = 'test-slug'
GROUP_SLUG_2 = 'group-2'
USERNAME = 'auth'
USERNAME_2 = 'auth_2'
NEXT = '{}?next={}'

URL_MAIN = reverse('posts:index')
URL_LOGIN = reverse('users:login')
URL_CREATE = reverse('posts:create')
URL_CREATE_REDIRECT = NEXT.format(URL_LOGIN, URL_CREATE)
URL_PROFILE = reverse('posts:profile', args=[USERNAME])
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_2 = User.objects.create_user(username=USERNAME_2)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа - 2',
            slug=GROUP_SLUG_2,
            description='Второе естовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.guest = Client()
        cls.another = Client()
        cls.another.force_login(cls.user_2)
        cls.form = PostForm()
        cls.comment_form = CommentForm()
        cls.URL_POST_EDIT = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.pk})
        cls.URL_POST_EDIT_REDIRECT = NEXT.format(URL_LOGIN, cls.URL_POST_EDIT)
        cls.URL_POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.pk})
        cls.URL_ADD_COMMENT = reverse('posts:add_comment', args=[cls.post.pk])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает пост"""
        image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый новый пост',
            'group': self.group.pk,
            'image': image,
        }
        response = self.authorized_client.post(
            URL_CREATE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, URL_PROFILE)
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        new_posts = Post.objects.exclude(pk=self.post.pk)
        self.assertEqual(new_posts.count(), 1)
        new_post = new_posts[0]
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(
            new_post.image.name, 'posts/' + form_data['image'].name)
        self.assertEqual(new_post.group.pk, form_data['group'])
        self.assertEqual(new_post.author, self.user)

    def test_guest_create_post(self):
        """Аноним не сможет создать пост."""
        posts_count = Post.objects.all().count()
        form_data = {
            'text': 'Тестовый новый пост',
            'group': self.group.pk,
        }
        response = self.guest.post(
            URL_CREATE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, URL_CREATE_REDIRECT)
        self.assertEqual(posts_count, Post.objects.all().count())

    def test_edit_post(self):
        """Валидная форма Сохраняет изменения"""
        image = SimpleUploadedFile(
            name='small_2.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый отредактированный текст',
            'group': self.group_2.pk,
            'image': image,
        }
        response = self.authorized_client.post(
            self.URL_POST_EDIT,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.URL_POST_DETAIL)
        edit_post = response.context['post']
        self.assertEqual(edit_post.text, form_data['text'])
        self.assertEqual(edit_post.group.pk, form_data['group'])
        self.assertEqual(edit_post.author, self.post.author)
        self.assertEqual(
            edit_post.image.name, 'posts/' + form_data['image'].name)

    def test_create_comment(self):
        """Валидная форма создает коментарий"""
        comments = set(Comment.objects.all())
        form_data = {
            'text': 'Тестовый коментарий',
        }
        response = self.authorized_client.post(
            self.URL_ADD_COMMENT,
            data=form_data,
            follow=True
        )
        comments = set(Comment.objects.all()) - comments
        self.assertRedirects(response, self.URL_POST_DETAIL)
        self.assertEqual(len(comments), 1)
        new_comment = comments.pop()
        self.assertEqual(new_comment.text, form_data['text'])
        self.assertEqual(new_comment.post, self.post)
        self.assertEqual(new_comment.author, self.user)

    def test_create_comment_anonymously(self):
        """Аноним не сможет создать комментарий."""
        count_comments = Comment.objects.all().count()
        form_data = {
            'text': 'Тестовый коментарий',
        }
        self.guest.post(
            self.URL_ADD_COMMENT,
            data=form_data,
            follow=True
        )
        self.assertEqual(count_comments, Comment.objects.all().count())

    def test_edir_post_anonymously(self):
        """Попытки анонима и не-автора отредактировать пост."""
        redirect_page_url = [
            [self.guest, self.URL_POST_EDIT_REDIRECT],
            [self.another, self.URL_POST_DETAIL],
        ]
        image = SimpleUploadedFile(
            name='small_3.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый отредактированный текст',
            'group': self.group_2.pk,
            'image': image,
        }
        for client, redirect_url in redirect_page_url:
            with self.subTest(client=client):
                response = client.post(
                    self.URL_POST_EDIT,
                    data=form_data,
                    follow=True
                )
                self.assertEqual(Post.objects.count(), 1)
                post = Post.objects.get(pk=self.post.pk)
                self.assertRedirects(response, redirect_url)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.image, self.post.image)
