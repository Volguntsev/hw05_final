import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Group, User
from ..settings import COUNT_POSTS_IN_PAGE

GROUP_SLUG = 'test-slug'
GROUP_SLUG_2 = 'group-2'
USERNAME = 'auth'

URL_MAIN = reverse('posts:index')
URL_GROUP = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
URL_GROUP_2 = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG_2})
URL_PROFILE = reverse('posts:profile', kwargs={'username': USERNAME})
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMAL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMAL_GIF,
            content_type='image/gif'
        )
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
            group=cls.group,
            image=cls.uploaded,
        )
        cls.URL_POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.pk})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PagesTests.user)

    def test_page_show_correct_context(self):
        """Шаблон index, group, profile сформирован с правильным контекстом."""
        Urls = [
            [URL_MAIN, 'page_obj'],
            [URL_GROUP, 'page_obj'],
            [URL_PROFILE, 'page_obj'],
            [self.URL_POST_DETAIL, 'post'],
        ]

        for address, var_context in Urls:
            with self.subTest(address=address):
                page = self.authorized_client.get(address).context[var_context]
                if (var_context == 'page_obj'):
                    self.assertEqual(len(page), 1)
                    post = page[0]
                else:
                    post = page
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(
                    post.image.name, 'posts/' + self.uploaded.name)
                self.assertEqual(post.pk, self.post.pk)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.author, self.post.author)

    def test_profile_page_correct_context(self):
        """Автор в контексте Профиля."""
        self.assertEqual(
            self.authorized_client.get(URL_PROFILE).context['author'],
            self.user)

    def test_group_page_correct_context(self):
        """Группа в контексте страницы группы."""
        group = self.authorized_client.get(URL_GROUP).context['group']
        self.assertEqual(group, self.group)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)

    def test_othet_group_page_correct_context(self):
        """Пост не попал на чужую Групп-ленту."""
        page = self.authorized_client.get(URL_GROUP_2).context['page_obj']
        self.assertNotIn(self.post, page)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.count_posts = COUNT_POSTS_IN_PAGE + 3
        Post.objects.bulk_create([Post(
            author=cls.user, text=f'Тестовый пост {i}', group=cls.group)
            for i in range(cls.count_posts)]
        )

    def setUp(self):
        self.guest_client = Client()

    def test_page_contains_records(self):
        paginator_ursl = {
            URL_MAIN: COUNT_POSTS_IN_PAGE,
            URL_GROUP: COUNT_POSTS_IN_PAGE,
            URL_PROFILE: COUNT_POSTS_IN_PAGE,
            URL_MAIN + '?page=2': self.count_posts - COUNT_POSTS_IN_PAGE,
            URL_GROUP + '?page=2': self.count_posts - COUNT_POSTS_IN_PAGE,
            URL_PROFILE + '?page=2': self.count_posts - COUNT_POSTS_IN_PAGE,
        }
        for address, count_posts in paginator_ursl.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']),
                    count_posts
                )
