from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User

GROUP_SLUG = 'test-slug'
USERNAME = 'auth'
USERNAME_2 = 'auth_2'
NEXT = '{}?next={}'

URL_MAIN = reverse('posts:index')
URL_CREATE = reverse('posts:create')
URL_GROUP = reverse('posts:group_list', args=[GROUP_SLUG])
URL_PROFILE = reverse('posts:profile', args=[USERNAME])
URL_LOGIN = reverse('users:login')
URL_CREATE_REDIRECT = NEXT.format(URL_LOGIN, URL_CREATE)
URL_FOLLOW = reverse('posts:follow_index')
URL_FOLLOW_REDIRECT = NEXT.format(URL_LOGIN, URL_FOLLOW)
URL_PROFILE_FOLLOW = reverse('posts:profile_follow', args=[USERNAME])
URL_PROFILE_FOLLOW_REDIRECT = NEXT.format(URL_LOGIN, URL_PROFILE_FOLLOW)
URL_PROFILE_UNFOLLOW = reverse('posts:profile_unfollow', args=[USERNAME])
URL_PROFILE_UNFOLLOW_REDIRECT = NEXT.format(URL_LOGIN, URL_PROFILE_UNFOLLOW)


class PostURLTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.guest = Client()
        cls.author = Client()
        cls.another = Client()
        cls.author.force_login(cls.user)
        cls.another.force_login(cls.user_2)
        cls.URL_POST_EDIT = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.pk})
        cls.URL_POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.pk})
        cls.URL_POST_EDIT_REDIRECT = NEXT.format(URL_LOGIN, cls.URL_POST_EDIT)

    def test_redirect_page(self):
        """Страницы перенаправляют пользователя"""
        redirect_page_url = [
            [self.URL_POST_EDIT, self.guest,
                self.URL_POST_EDIT_REDIRECT],
            [self.URL_POST_EDIT, self.another,
                self.URL_POST_DETAIL],
            [URL_CREATE, self.guest, URL_CREATE_REDIRECT],
            [URL_FOLLOW, self.guest, URL_FOLLOW_REDIRECT],
            [URL_PROFILE_FOLLOW, self.guest, URL_PROFILE_FOLLOW_REDIRECT],
            [URL_PROFILE_UNFOLLOW, self.guest, URL_PROFILE_UNFOLLOW_REDIRECT],
            [URL_PROFILE_FOLLOW, self.another, URL_PROFILE],
            [URL_PROFILE_UNFOLLOW, self.another, URL_PROFILE],
            [URL_PROFILE_FOLLOW, self.author, URL_PROFILE],
        ]
        for address, client, redirect_url in redirect_page_url:
            with self.subTest(address=address, user=client):
                self.assertRedirects(
                    client.get(address, follow=True), redirect_url
                )

    def test_urls_clients(self):
        """Страницы доступныt для гостя и для авторизованного пользователя """
        code_page_url = [
            [URL_MAIN, self.guest, 200],
            [URL_GROUP, self.guest, 200],
            [URL_PROFILE, self.guest, 200],
            [self.URL_POST_DETAIL, self.guest, 200],
            ['/unexisting_page/', self.guest, 404],
            [self.URL_POST_EDIT, self.guest, 302],
            [URL_CREATE, self.guest, 302],
            [self.URL_POST_EDIT, self.another, 302],
            [URL_CREATE, self.author, 200],
            [self.URL_POST_EDIT, self.author, 200],
            [URL_PROFILE_FOLLOW, self.another, 302],
            [URL_PROFILE_UNFOLLOW, self.another, 302],
            [URL_PROFILE_FOLLOW, self.guest, 302],
            [URL_PROFILE_UNFOLLOW, self.guest, 302],
            [URL_PROFILE_FOLLOW, self.author, 302],
            [URL_PROFILE_UNFOLLOW, self.author, 404],
            [URL_FOLLOW, self.another, 200],
            [URL_FOLLOW, self.guest, 302],
        ]

        for address, client, code in code_page_url:
            with self.subTest(address=address, user=client):
                self.assertEqual(
                    client.get(address).status_code, code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            URL_MAIN: 'posts/index.html',
            URL_GROUP: 'posts/group_list.html',
            URL_PROFILE: 'posts/profile.html',
            URL_CREATE: 'posts/create_post.html',
            self.URL_POST_DETAIL: 'posts/post_detail.html',
            self.URL_POST_EDIT: 'posts/create_post.html',
            URL_FOLLOW: 'posts/follow.html',
            '/unexisting_page/': 'core/404.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.author.get(address), template)
