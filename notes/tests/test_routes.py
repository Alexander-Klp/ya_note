from django.test import TestCase
from notes.models import Note
from http import HTTPStatus
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()


class TestRoutes(TestCase):
    """Тестирование маршрутов"""
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=cls.author
        )
        cls.login_url = reverse('users:login')

    def test_successful_creation(self):
        """Проверка создания заметки"""
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)

    def test_pages_availability(self):
        """Доступность домашней страницы,логина,логаута для анонимуса"""
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_notes_add_list(self):
        """
        Доступность страницы добавления заметок и списка заметок
        для автора и анонимного пользователя
        """
        users_statuses = (
            (self.reader, HTTPStatus.FOUND),
            (self.author, HTTPStatus.OK),
        )
        urls = ('notes:add', 'notes:list')
        for user, status in users_statuses:
            if user == self.author:
                self.client.force_login(user)
            for name in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=None)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_availability_notes_detail_edit_delete(self):
        """
        Проверка доступности страниц заметки детально,
        удаление и редактирование.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        urls = ('notes:edit', 'notes:delete', 'notes:detail')
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        Анонимного пользователя перенесет на страницу логина
        при попытке зайти на страницы работы с заметкой
        """
        urls = (
            ('notes:add', None),
            ('notes:list', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:detail', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{self.login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
