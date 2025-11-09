import pytest
from django.contrib.auth.models import User
from app.models import Article
from uuid import UUID


@pytest.fixture
def test_user(db):
    """テスト用ユーザーのフィクスチャ"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_article(db, test_user):
    """テスト用記事のフィクスチャ"""
    return Article.objects.create(
        title='テスト記事',
        content='これはテスト記事の本文です。',
        user=test_user
    )


@pytest.mark.django_db
class TestArticleModel:
    """Articleモデルのテスト"""

    def test_article_creation(self, test_article):
        """記事が正しく作成されることを確認"""
        assert isinstance(test_article, Article)
        assert test_article.title == 'テスト記事'
        assert test_article.content == 'これはテスト記事の本文です。'

    def test_article_id_is_uuid(self, test_article):
        """記事のIDがUUIDであることを確認"""
        assert isinstance(test_article.id, UUID)

    def test_article_str_method(self, test_article):
        """__str__メソッドがタイトルを返すことを確認"""
        assert str(test_article) == 'テスト記事'

    def test_article_has_timestamps(self, test_article):
        """記事が作成日時と更新日時を持つことを確認"""
        assert test_article.created_at is not None
        assert test_article.updated_at is not None

    def test_article_title_max_length(self, test_article):
        """タイトルの最大長が正しく設定されていることを確認"""
        max_length = test_article._meta.get_field('title').max_length
        assert max_length == 200

    def test_article_content_is_text_field(self, test_article):
        """本文がTextFieldであることを確認"""
        field_type = test_article._meta.get_field('content').get_internal_type()
        assert field_type == 'TextField'

    def test_article_verbose_names(self, test_article):
        """フィールドのverbose_nameが正しく設定されていることを確認"""
        assert test_article._meta.get_field('title').verbose_name == 'タイトル'
        assert test_article._meta.get_field('content').verbose_name == '本文'
        assert test_article._meta.get_field('created_at').verbose_name == '作成日時'
        assert test_article._meta.get_field('updated_at').verbose_name == '更新日時'

    def test_article_meta_verbose_name(self, test_article):
        """Metaのverbose_nameが正しく設定されていることを確認"""
        assert test_article._meta.verbose_name == '記事'
        assert test_article._meta.verbose_name_plural == '記事'

    def test_article_user_relationship(self, test_article, test_user):
        """記事とユーザーの関連が正しく設定されていることを確認"""
        assert test_article.user == test_user
        assert test_article in test_user.articles.all()

    def test_article_ordering(self, db, test_user):
        """記事が作成日時の降順で並ぶことを確認"""
        article1 = Article.objects.create(
            title='記事1',
            content='内容1',
            user=test_user
        )
        article2 = Article.objects.create(
            title='記事2',
            content='内容2',
            user=test_user
        )
        articles = Article.objects.all()
        assert articles[0] == article2
        assert articles[1] == article1
