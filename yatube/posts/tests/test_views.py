from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from http import HTTPStatus
from yatube.settings import num_posts

from posts.models import Post, Group, User


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаём авторизованного пользователя
        cls.user = User.objects.create_user(username='StasBasov')
        # Создаём группу в бд
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        # Создаём запись в бд
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        PostViewsTest.authorized_client = Client()
        PostViewsTest.authorized_client.force_login(self.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "reverse(name): имя_html_шаблона"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',

            (reverse('posts:group_list', kwargs={
                'slug': PostViewsTest.group.slug})):
                    'posts/group_list.html',

            (reverse('posts:user', kwargs={
                'username': 'StasBasov'})): 'posts/profile.html',

            (reverse('posts:post_detail', kwargs={
                'post_id': self.post.id})): 'posts/post_detail.html',

            (reverse('posts:post_edit', kwargs={
                'post_id': self.post.id})): 'posts/create_post.html',

            reverse('posts:post_create'): 'posts/create_post.html',
        }
        # Проверяем, что при обращении к name вызывается соответствующий шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_index_page_show_correct_context(self):
        """Проверка контекста index."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_object = response.context['page_obj'][0]
        self.assertEqual(post_object.text[:15], f'{PostViewsTest.post.text}')
        self.assertEqual(
            str(post_object.group),
            f'{PostViewsTest.group.title}'
        )

    def test_group_list_show_correct_context(self):
        """Проверка контекста group_list."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{PostViewsTest.group.slug}'}
            )
        )
        self.assertIn('page_obj', response.context)
        post = response.context['page_obj'][0]
        self.assertEqual(str(post.author), 'StasBasov')
        # Не могу написать в слаке так как нет общих каналов
        # Если писать (PostViewsTest.user, 'StasBasov')
        # AssertionError: <User: StasBasov> != 'StasBasov'
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(str(post.group), 'Тестовая группа')

    def test_profile_show_correct_context(self):
        """Проверка контекста profile"""
        response = self.authorized_client.get(
            reverse(
                'posts:user',
                kwargs={'username': 'StasBasov'}
            )
        )
        post_object = response.context['page_obj'].object_list[0]
        self.assertEqual(post_object.text, 'Тестовый текст')
        self.assertEqual(str(post_object.group), 'Тестовая группа')
        self.assertEqual(post_object.group.slug, 'test-slug')
        self.assertEqual(str(post_object.author), 'StasBasov')

    def test_post_detail_show_correct_context(self):
        """Проверка контекста post_detail."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            )
        )
        post_object = response.context['post'].id
        self.assertEqual(self.post.id, post_object)

    def test_post_edit_show_correct_context(self):
        """Проверка контекста post_edit."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context(self):
        """Проверка контекста create_post."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_exists(self):
        """Новый пост появляется на страницах index, group_list,
        profile, если при его создании указать группу.
        """
        urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:user', kwargs={'username': 'StasBasov'}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                post = response.context['page_obj'][0]
                self.assertEqual(post.text, 'Тестовый текст')
                self.assertEqual(str(post.author), 'StasBasov')
                self.assertEqual(str(post.group), 'Тестовая группа')

    def test_new_post_absence(self):
        """Пост не попал в группу, для которой не был предназначен."""
        PostViewsTest.group_two = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-two',
            description='Тестовое описание',
        )
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.context.get('page_obj')[0].group,
                            self.group_two)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUp(self):
        super().setUpClass()
        self.user = User.objects.create_user(username='StasBasov')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        posts = []
        for i in range(13):
            posts.append(
                Post(text=f'Тестовый текст {i}',
                     group=self.group, author=self.user)
            )
        Post.objects.bulk_create(posts)

    def test_first_index_page_contains_ten_records(self):
        """На первую страницу index выводится 10 постов из 13"""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), num_posts)

    def test_second_index_page_contains_three_records(self):
        """На вторую страницу index выводятся оставшиеся 3 поста"""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_group_page_contains_ten_records(self):
        """На первую страницу group_list выводится 10 постов из 13"""
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            )
        )
        self.assertEqual(len(response.context['page_obj']), num_posts)

    def test_second_group_page_contains_three_records(self):
        """На вторую страницу group_list выводятся оставшиеся 3 поста"""
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_profile_page_contains_three_records(self):
        """На первую страницу profile выводится 10 постов из 13"""
        response = self.client.get(
            reverse(
                'posts:user',
                kwargs={'username': 'StasBasov'}
            )
        )
        self.assertEqual(len(response.context['page_obj']), num_posts)
        # num_posts уже константа в settings.py

    def test_second_profile_page_contains_three_records(self):
        """На вторую страницу profile выводятся оставшиеся 3 поста"""
        response = self.client.get(
            reverse(
                'posts:user',
                kwargs={'username': 'StasBasov'}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)
