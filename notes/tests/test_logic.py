from http import HTTPStatus

from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNotesCreation(TestCase):
    """Тест создания заметки"""
    TITLE = 'Заголовок'
    SLUG = 'slug'
    TEXT = 'Текст'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.url_add = reverse('notes:add')
        cls.url_done = reverse('notes:success')
        cls.form_data = {
            'title': cls.TITLE,
            'text': cls.TEXT,
            'slug': cls.SLUG,
        }

    def test_anonymous_user_cant_create_notes(self):
        """Ананимус не может создавать заметки"""
        self.client.post(self.url_add, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_notes(self):
        """пользователь может создать заметку"""
        response = self.auth_client.post(self.url_add, data=self.form_data)
        self.assertRedirects(response, self.url_done)
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.TITLE)
        self.assertEqual(note.text, self.TEXT)
        self.assertEqual(note.slug, self.SLUG)
        self.assertEqual(note.author, self.user)

    def test_empty_slug(self):
        self.form_data.pop(self.SLUG)
        response = self.auth_client.post(self.url_add, data=self.form_data)
        self.assertRedirects(response,  self.url_done)
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    """Тест редактирование и удаления заметки, проверка уникальности slug"""
    TEXT = 'Текст'
    NEW_TEXT = 'Обновлённый текст'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор комментария')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text=cls.TEXT,
            slug='slug',
            author=cls.author
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {
            'title': cls.note.title,
            'text': cls.NEW_TEXT,
            'slug': 'slug',
        }
        cls.url_done = reverse('notes:success')
        cls.url_add = reverse('notes:add')

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку"""
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.url_done)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        """Другой пользователь не может удалить заметки автора"""
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку"""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.url_done)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        """Другой пользователь не может редактировать заметку пользователя"""
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.TEXT)

    def test_not_unique_slug(self):
        """Тест добавление одинакого slug"""
        self.form_data['slug'] = self.note.slug
        response = self.reader_client.post(self.url_add, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=f'{self.note.slug}{WARNING}'
        )
