from django.test import TestCase

from ..models import Group, Post, User, POST_STR

GROUP_SLUG = 'test-slug'
USERNAME = 'auth'


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_group_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.group.title, str(self.group))

    def test_models_post_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_object_name = (POST_STR.format(
            text=self.post.text[:200],
            pub_date=self.post.pub_date,
            group=self.post.group,
            author=self.post.author.get_full_name())
        )
        self.assertEqual(expected_object_name, str(self.post))
