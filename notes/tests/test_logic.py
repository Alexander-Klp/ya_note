from django.test import TestCase, Client
from notes.models import Note
from django.urls import reverse
from django.contrib.auth import get_user_model
from http import HTTPStatus
from notes.forms import WARNING

from django.core.exceptions import ValidationError

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
        self.client.post(self.url_add, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_notes(self):
        response = self.auth_client.post(self.url_add, data=self.form_data)
        self.assertRedirects(response, self.url_done)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.TITLE)
        self.assertEqual(note.text, self.TEXT)
        self.assertEqual(note.slug, self.SLUG)
        self.assertEqual(note.author, self.user)

class TestNoteEditDelete(TestCase):
    """Тест редактирование и удаления заметки"""

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
            'title': cls.note,
            'text': cls.NEW_TEXT,
        }
        cls.url_done = reverse('notes:success')

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


class TestSlugNote(TestCase):
    """Слаготест"""
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор №1')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Автор №2')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note1 = Note.objects.create(
            title='Заголовок1',
            text='Текст1',
            slug='slug1',
            author=cls.author
        )
        cls.note2 = Note.objects.create(
            title='Заголовок2',
            text='Текст2',
            slug='slug2',
            author=cls.reader
        )
        cls.form_data = {
            'title': cls.note2.title,
            'text': cls.note2.text,
            'slug': cls.note1.slug,
        }

    def test_slug_unique(self):
        """
        Автор №2 хочет сделать такой же slug,
        который уэже существует у Автора №1
        """
        edit_url = reverse('notes:edit', args=(self.note2.slug,))
        response = self.reader_client.post(edit_url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=f'{self.note1.slug}{WARNING}'
        )
