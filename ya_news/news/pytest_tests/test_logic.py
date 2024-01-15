from http import HTTPStatus

from django.urls import reverse

import pytest

from pytest_django.asserts import assertRedirects, assertFormError

from news.models import Comment
from news.forms import BAD_WORDS, WARNING


# Анонимный пользователь не может отправить комментарий.
@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, new_comment, news):
    url = reverse('news:detail', args=(news.pk,))
    client.post(url, data=new_comment)
    assert Comment.objects.count() == 0


# Авторизованный пользователь может отправить комментарий.
def test_user_can_create_comment(author_client, author, new_comment,
                                 news):
    url = reverse('news:detail', args=(news.pk,))
    author_client.post(url, data=new_comment)
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == new_comment['text']
    assert comment.news == news
    assert comment.author == author


# Если комментарий содержит запрещённые слова, он не будет опубликован,
# а форма вернёт ошибку.
def test_user_cant_use_bad_words(author_client, news):
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    url = reverse('news:detail', args=(news.pk,))
    response = author_client.post(url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0


# Авторизованный пользователь может редактировать или удалять свои комментарии.
def test_author_can_edit_comment(author_client, new_comment, news,
                                 comment):
    news_url = reverse('news:detail', args=(news.pk,))
    comment_url = reverse('news:edit', args=(comment.pk,))
    response = author_client.post(comment_url, data=new_comment)
    assertRedirects(response, news_url + '#comments')
    comment.refresh_from_db()
    assert comment.text == new_comment['text']


def test_author_can_delete_comment(author_client, news, comment):
    news_url = reverse('news:detail', args=(news.pk,))
    comments_url = reverse('news:delete', args=(comment.pk,))
    response = author_client.delete(comments_url)
    assertRedirects(response, news_url + '#comments')
    comments_count = Comment.objects.count()
    assert comments_count == 0


# Авторизованный пользователь не может редактировать или удалять чужие
# комментарии.
def test_user_cant_edit_comment_of_another_user(admin_client, new_comment,
                                                comment):
    comment_url = reverse('news:edit', args=(comment.pk,))
    response = admin_client.post(comment_url, data=new_comment)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == 'Текст комментария'


def test_user_cant_delete_comment_of_another_user(admin_client, comment):
    comment_url = reverse('news:delete', args=(comment.pk,))
    response = admin_client.delete(comment_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1
