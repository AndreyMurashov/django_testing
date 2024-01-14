from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.notes = Note.objects.create(title='Заголовок',
                                        text='Текст заметки',
                                        author=cls.author)

# Главная страница доступна анонимному пользователю.
    def test_home_page(self):
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

# Аутентифицированному пользователю доступна страница со списком
# заметок notes/, страница успешного добавления заметки done/,
# страница добавления новой заметки add/.
    def test_availability_list_done_add_pages(self):
        user = self.author
        self.client.force_login(user)
        for name in (
                'notes:list',
                'notes:success',
                'notes:add',
        ):
            with self.subTest(user=user, name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

# Страницы отдельной заметки, удаления и редактирования заметки
# доступны только автору заметки. Если на эти страницы попытается
# зайти другой пользователь — вернётся ошибка 404.
    def test_availability_detail_delete_edit_pages(self):
        user_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND)
        )
        for user, status in user_statuses:
            self.client.force_login(user)
            for name in (
                    'notes:detail',
                    'notes:delete',
                    'notes:edit',
            ):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.notes.slug, ))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

# При попытке перейти на страницу списка заметок, страницу успешного
# добавления записи, страницу добавления заметки, отдельной заметки,
# редактирования или удаления заметки анонимный пользователь
# перенаправляется на страницу логина.
    def test_redirect_for_anonymous_client(self):
        urls = (
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
            ('notes:detail', (self.notes.slug, )),
            ('notes:delete', (self.notes.slug, )),
            ('notes:edit', (self.notes.slug, )),
        )

        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'/auth/login/?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

# Страницы регистрации пользователей, входа в учётную запись и
# выхода из неё доступны всем пользователям.
    def test_availability_reg_in_out_pages(self):
        user_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.OK)
        )
        for user, status in user_statuses:
            self.client.force_login(user)
            for name in (
                    'users:signup',
                    'users:login',
                    'users:logout',
            ):
                with self.subTest(user=user, name=name):
                    url = reverse(name)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)
