from django.test import TestCase, Client
from http import HTTPStatus
from posts.models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()

        self.author_client = Client()
        self.author_client.force_login(self.user)

    def page_accessibility_test(self):
        url_names = ('/', f'/group/{self.group.slug}/',
                     f'/profile/{self.user}/', f'/posts/{self.post.id}/')
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_urls_HTTPStatus(self):
        response = self.author_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            ('posts/index.html', '/'),
            ('posts/group_list.html', f'/group/{self.group.slug}/'),
            ('posts/profile.html', f'/profile/{self.user}/'),
            ('posts/post_detail.html', f'/posts/{self.post.id}/'),
        )
        for template, address in templates_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def accessibility_of_the_edit_page(self):
        response = self.author_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_unexisting_page_url_exists_at_desired_location(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_author_url_uses_correct_template(self):
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_guest_redirect(self):
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_no_author_redirect(self):
        self.no_author = User.objects.create_user(username='no_author')
        self.no_author_client = Client()
        self.no_author_client.force_login(self.no_author)

        response = self.no_author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
