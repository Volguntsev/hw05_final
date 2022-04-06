import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, User
from ..settings import SMALL_GIF

GROUP_SLUG = 'test-slug'
GROUP_SLUG_2 = 'group-2'
USERNAME = 'auth'

URL_MAIN = reverse('posts:index')
URL_CREATE = reverse('posts:create')
URL_PROFILE = reverse('posts:profile', args=[USERNAME])
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
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
        cls.authorized_client.force_login(PostCreateFormTests.user)
        cls.form = PostForm()
        cls.comment_form = CommentForm()
        cls.URL_POST_EDIT = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.pk})
        cls.URL_POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.pk})
        cls.URL_ADD_COMMENT = reverse('posts:add_comment', args=[cls.post.pk])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись"""
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
        self.assertTrue(new_posts.count() == 1)
        new_post = new_posts[0]
        self.assertTrue(new_post.text == form_data['text'])
        self.assertEqual(
            new_post.image.name, 'posts/' + image.name)
        self.assertTrue(new_post.group.pk == form_data['group'])
        self.assertTrue(new_post.author == self.user)

    def test_edit_post(self):
        """Валидная форма Сохраняет изменения"""
        image = SimpleUploadedFile(
            name='small.gif',
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
        self.assertTrue(edit_post.text == form_data['text'])
        self.assertTrue(edit_post.group.pk == form_data['group'])
        self.assertTrue(edit_post.author == self.post.author)
        self.assertTrue(
            edit_post.image.name, 'posts/' + image.name)

    def test_create_comment(self):
        """Валидная форма создает коментарий"""
        tasks_count = self.post.comments.count()
        form_data = {
            'text': 'Тестовый коментарий',
        }
        response = self.authorized_client.post(
            self.URL_ADD_COMMENT,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.URL_POST_DETAIL)
        self.assertEqual(self.post.comments.count(), tasks_count + 1)
        self.assertTrue(self.post.comments.count() == 1)
        self.assertTrue(self.post.comments.all()[0].text == form_data['text'])
