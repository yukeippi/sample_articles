from uuid import UUID

import pytest

from app.models import Article
from app.tests.factories import ArticleFactory


@pytest.mark.django_db
class TestArticleModel:
    """Articleモデルのテスト"""

    def test_article_creation(self, article):
        """記事が正しく作成されることを確認"""
        assert isinstance(article, Article)
        assert article.title
        assert article.content
        assert article.user is not None

    def test_article_creation_with_custom_values(self):
        """カスタム値で記事が作成されることを確認"""
        article = ArticleFactory.create(title='カスタムタイトル', content='カスタム本文')
        assert article.title == 'カスタムタイトル'
        assert article.content == 'カスタム本文'

    def test_article_id_is_uuid(self, article):
        """記事のIDがUUIDであることを確認"""
        assert isinstance(article.id, UUID)

    def test_article_str_method(self, article):
        """__str__メソッドがタイトルを返すことを確認"""
        assert str(article) == article.title

    def test_article_has_timestamps(self, article):
        """記事が作成日時と更新日時を持つことを確認"""
        assert article.created_at is not None
        assert article.updated_at is not None

    def test_article_title_max_length(self, article):
        """タイトルの最大長が正しく設定されていることを確認"""
        max_length = article._meta.get_field('title').max_length
        assert max_length == 200

    def test_article_content_is_text_field(self, article):
        """本文がTextFieldであることを確認"""
        field_type = article._meta.get_field('content').get_internal_type()
        assert field_type == 'TextField'

    def test_article_verbose_names(self, article):
        """フィールドのverbose_nameが正しく設定されていることを確認"""
        assert article._meta.get_field('title').verbose_name == 'タイトル'
        assert article._meta.get_field('content').verbose_name == '本文'
        assert article._meta.get_field('created_at').verbose_name == '作成日時'
        assert article._meta.get_field('updated_at').verbose_name == '更新日時'

    def test_article_meta_verbose_name(self, article):
        """Metaのverbose_nameが正しく設定されていることを確認"""
        assert article._meta.verbose_name == '記事'
        assert article._meta.verbose_name_plural == '記事'

    def test_article_user_relationship(self, article):
        """記事とユーザーの関連が正しく設定されていることを確認"""
        assert article.user is not None
        assert article in article.user.articles.all()

    def test_article_ordering(self, user):
        """記事が作成日時の降順で並ぶことを確認"""
        article1 = ArticleFactory.create(user=user, title='記事1')
        article2 = ArticleFactory.create(user=user, title='記事2')
        articles = Article.objects.all()
        # 最後に作成された記事が最初に来る
        assert articles[0] == article2
        assert articles[1] == article1
