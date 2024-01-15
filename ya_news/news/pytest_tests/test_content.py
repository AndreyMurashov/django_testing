from django.conf import settings
from django.urls import reverse

import pytest


# Количество новостей на главной странице — не более 10.
@pytest.mark.django_db
def test_news_count(client, news_list):
    url = reverse('news:home')
    response = client.get(url)
    news_count = response.context['object_list'].count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


# Новости отсортированы от самой свежей к самой старой.
# Свежие новости в начале списка.
@pytest.mark.django_db
def test_news_list_order(client, news_list):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    all_news = [news for news in object_list]
    sorted_news = sorted(all_news, key=lambda x: x.date, reverse=True)
    assert sorted_news == news_list


# Комментарии на странице отдельной новости отсортированы в
# хронологическом порядке: старые в начале списка, новые — в конце.
@pytest.mark.django_db
def test_comments_list_order(client, news, comments_list):
    url = reverse('news:detail', args=(news.pk,))
    response = client.get(url)
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    for i in range(len(all_comments) - 1):
        assert all_comments[i].created < all_comments[i + 1].created


# Анонимному пользователю недоступна форма для отправки комментария на
# странице отдельной новости, а авторизованному доступна.
@pytest.mark.parametrize(
    'clients, status',
    (
        (pytest.lazy_fixture('author_client'), True),
        (pytest.lazy_fixture('client'), False),
    ),
)
@pytest.mark.django_db
def test_anonymous_client_has_no_form(clients, status, comment):
    url = reverse('news:detail', args=(comment.pk,))
    response = clients.get(url)
    assert ('form' in response.context) is status
