from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from datetime import datetime, timedelta

import pytest

from news.models import News, Comment


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author, client):
    client.force_login(author)
    return client


@pytest.fixture
def news():
    news = News.objects.create(
        title='Заголовок',
        text='Текст новости',
        date=datetime.today(),
    )
    return news


@pytest.fixture
def news_list():
    today, list_news = datetime.today(), []
    for index in range(settings.NEWS_COUNT_ON_HOME_PAGE):
        news = News.objects.create(
            title='Новость {index}',
            text='Текст новости',
        )
        news.date = today - timedelta(days=index)
        news.save()
        list_news.append(news)
    return list_news


@pytest.fixture
def comment(news, author):
    comment = Comment.objects.create(
        text='Текст комментария',
        news=news,
        author=author
    )
    return comment


@pytest.fixture
def comments_list(news, author):
    now, list_comment = timezone.now(), []
    for index in range(2):
        comment = Comment.objects.create(
            text='Текст {index}',
            news=news,
            author=author,
        )
        comment.created = now + timedelta(days=index)
        comment.save()
        list_comment.append(comment)


# Количество новостей на главной странице — не более 10.
@pytest.mark.django_db
def test_news_count(client, news_list):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    news_count = len(object_list)
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
    assert all_comments[0].created < all_comments[1].created


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
