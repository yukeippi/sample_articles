from django.test import TestCase
from app.models import Article
from uuid import UUID


class ArticleModelTest(TestCase):
    """Articleモデルのテスト"""

    def setUp(self):
        """テストデータのセットアップ"""
        self.article = Article.objects.create(
            title='テスト記事',
            content='これはテスト記事の本文です。'
        )

    def test_article_creation(self):
        """記事が正しく作成されることを確認"""
        self.assertIsInstance(self.article, Article)
        self.assertEqual(self.article.title, 'テスト記事')
        self.assertEqual(self.article.content, 'これはテスト記事の本文です。')

    def test_article_id_is_uuid(self):
        """記事のIDがUUIDであることを確認"""
        self.assertIsInstance(self.article.id, UUID)

    def test_article_str_method(self):
        """__str__メソッドがタイトルを返すことを確認"""
        self.assertEqual(str(self.article), 'テスト記事')

    def test_article_has_timestamps(self):
        """記事が作成日時と更新日時を持つことを確認"""
        self.assertIsNotNone(self.article.created_at)
        self.assertIsNotNone(self.article.updated_at)

    def test_article_title_max_length(self):
        """タイトルの最大長が正しく設定されていることを確認"""
        max_length = self.article._meta.get_field('title').max_length
        self.assertEqual(max_length, 200)

    def test_article_content_is_text_field(self):
        """本文がTextFieldであることを確認"""
        field_type = self.article._meta.get_field('content').get_internal_type()
        self.assertEqual(field_type, 'TextField')

    def test_article_verbose_names(self):
        """フィールドのverbose_nameが正しく設定されていることを確認"""
        self.assertEqual(
            self.article._meta.get_field('title').verbose_name, 'タイトル'
        )
        self.assertEqual(
            self.article._meta.get_field('content').verbose_name, '本文'
        )
        self.assertEqual(
            self.article._meta.get_field('created_at').verbose_name, '作成日時'
        )
        self.assertEqual(
            self.article._meta.get_field('updated_at').verbose_name, '更新日時'
        )

    def test_article_meta_verbose_name(self):
        """Metaのverbose_nameが正しく設定されていることを確認"""
        self.assertEqual(self.article._meta.verbose_name, '記事')
        self.assertEqual(self.article._meta.verbose_name_plural, '記事')
