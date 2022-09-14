from posts.models import Group, Post, User
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
import shutil
import tempfile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author = User.objects.create_user(
            username='VeryFire'
        )
        PostCreateFormTests.post = Post.objects.create(
            author=self.author,
            text='text',
        )
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'text',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertRedirects(response, reverse('posts:user',
                             kwargs={'username':
                                     f'{self.author}'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(self.post.text, 'text')
        self.assertEqual(PostCreateFormTests.group, self.group)

    def test_edit_post(self):
        form_data = {
            'text': 'Отредактированный пост',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                id=self.post.id,
                group=self.group,
                text='Отредактированный пост',
            ).exists()
        )
