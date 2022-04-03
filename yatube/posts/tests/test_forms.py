import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from posts.models import Post, Group, User

GROUP_SLUG = 'test-slug'
GROUP_SLUG_2 = 'group-2'
USERNAME = 'auth'

URL_MAIN = reverse('posts:index')
URL_CREATE = reverse('posts:create')
URL_PROFILE = reverse('posts:profile', kwargs={'username': USERNAME})
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
        cls.form = PostForm()
        cls.URL_POST_EDIT = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.pk})
        cls.URL_POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.pk})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый новый пост',
            'group': self.group.pk,
            'image': uploaded
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
            new_post.image.name, 'posts/' + form_data['image'].name)
        self.assertTrue(new_post.group.pk == form_data['group'])
        self.assertTrue(new_post.author == self.user)

    def test_edit_post(self):
        """Валидная форма Сохраняет изменения"""
        form_data = {
            'text': 'Тестовый отредактированный текст',
            'group': self.group_2.pk,
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
