from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestNotesList(TestCase):
    """Тестирование контента на странице списка заметок"""
    NOTES_LIST_URL = reverse('notes:list')
    NOTES = 100

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        Note.objects.bulk_create(
            Note(
                title='Заголовок',
                text='Текст',
                slug=f'slug_{index}',
                author=cls.author
            )
            for index in range(cls.NOTES)
        )

    def test_notes_for_different_users(self):
        """Автор видит свои записи, а читатель не видит записей автора"""
        users_count_notes = (
            (self.author, self.NOTES),
            (self.reader, 0),
        )
        for user, count_notes in users_count_notes:
            self.client.force_login(user)
            for name in self.NOTES_LIST_URL:
                with self.subTest(user=user, name=name):
                    response = self.client.get(self.NOTES_LIST_URL)
                    object_list = response.context['object_list']
                    self.assertEqual(len(object_list), count_notes)


class TestForm(TestCase):
    """Тестирование форм"""
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=cls.author
        )
        cls.login_url = reverse('users:login')

    def test_pages_contains_form(self):
        """Форма передается"""
        urls = (
                ('notes:add', None),
                ('notes:edit', (self.note.slug,)),
            )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                assert 'form' in response.context
