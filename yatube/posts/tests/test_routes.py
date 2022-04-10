from django.test import TestCase
from django.urls import reverse

from ..urls import app_name

GROUP_SLUG = 'test-slug'
USERNAME = 'auth'
POST_ID = 7

URLS_PAGES_NAMES = [
    ['index', '/', {}],
    ['create', '/create/', {}],
    ['group_list', f'/group/{GROUP_SLUG}/', [GROUP_SLUG]],
    ['profile', f'/profile/{USERNAME}/', [USERNAME]],
    ['post_detail', f'/posts/{POST_ID}/', [POST_ID]],
    ['post_edit', f'/posts/{POST_ID}/edit/', [POST_ID]],
    ['add_comment', f'/posts/{POST_ID}/comment/', [POST_ID]],
    ['follow_index', '/follow/', []],
    ['profile_follow', f'/profile/{USERNAME}/follow/', [USERNAME]],
    ['profile_unfollow', f'/profile/{USERNAME}/unfollow/', [USERNAME]],
]


class URLSTests(TestCase):
    def test_routes_url(self):
        """Расчеты дают ожидаемые URL-адреса"""
        for name, url, args in URLS_PAGES_NAMES:
            with self.subTest(url=url):
                self.assertEqual(reverse(f'{app_name}:{name}', args=args), url)
