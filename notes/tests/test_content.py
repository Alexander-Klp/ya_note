from django.test import TestCase
from notes.models import Note
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()


class TestNotesList(TestCase):
    """Тестирование контента на странице списка заметок"""
    NOTES_LIST_URL = reverse('notes:list')
    NOTES = 100

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.login_url = reverse('users:login')
        Note.objects.bulk_create(
            Note(
                title='Заголовок',
                text='Текст',
                slug=f'slug_{index}',
                author=cls.author
            )
            for index in range(cls.NOTES)
        )

    def test_notes_count(self):
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
