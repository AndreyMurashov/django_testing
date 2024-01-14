from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Пользователь простой')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.notes = {
            'title': 'Заголовок 2',
            'text': 'Текст заметки',
            'slug': 'slug2'
        }

# Залогиненный пользователь может создать заметку.
    def test_user_can_create_note(self):
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.notes)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.title, self.notes['title'])
        self.assertEqual(new_note.text, self.notes['text'])
        self.assertEqual(new_note.slug, self.notes['slug'])
        self.assertEqual(new_note.author, self.author)

# Анонимный пользователь не может создать заметку.
    def test_anonymous_user_cant_create_note(self):
        url = reverse('notes:add')
        response = self.client.post(url, self.notes)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 0)

# Невозможно создать две заметки с одинаковым slug.
    def test_not_unique_slug(self):
        self.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=self.author,
        )
        url = reverse('notes:add')
        response = self.author_client.post(url, data={
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': self.note.slug
        })
        self.assertFormError(response, 'form', 'slug',
                             errors=(self.note.slug + WARNING))
        self.assertEqual(Note.objects.count(), 1)

# Если при создании заметки не заполнен slug, то он формируется
# автоматически, с помощью функции pytils.translit.slugify
    def test_empty_slug(self):
        url = reverse('notes:add')
        self.notes.pop('slug')
        response = self.author_client.post(url, self.notes)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.notes['title'])
        self.assertEqual(new_note.slug, expected_slug)

# Пользователь может удалять свои заметки.
    def test_author_can_delete_note(self):
        self.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=self.author,
        )
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

# Пользователь не может удалять чужие заметки.
    def test_other_user_cant_delete_note(self):
        self.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=self.author,
        )
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.reader_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

# Пользователь может редактировать свои заметки.
    def test_author_can_edit_note(self):
        self.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=self.author,
        )
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(url, self.notes)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.notes['title'])
        self.assertEqual(self.note.text, self.notes['text'])
        self.assertEqual(self.note.slug, self.notes['slug'])

# Пользователь не может редактировать чужие заметки.
    def test_other_user_cant_edit_note(self):
        self.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=self.author,
        )
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.reader_client.post(url, self.notes)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertNotEqual(self.note.title, self.notes['title'])
        self.assertNotEqual(self.note.text, self.notes['text'])
        self.assertNotEqual(self.note.slug, self.notes['slug'])
