# テストガイド

このディレクトリには、アプリケーションのテストコードが含まれています。

## テスト環境

- **pytest**: テストフレームワーク
- **pytest-django**: Django用のpytestプラグイン
- **faker**: ランダムなテストデータ生成
- **model-bakery**: Djangoモデルのファクトリライブラリ

## ディレクトリ構造

```
app/tests/
├── __init__.py
├── README.md                      # このファイル（テストガイド）
├── conftest.py                    # pytestのfixturesを定義
├── factories.py                   # model-bakeryを使ったファクトリクラス
├── test_factories_example.py      # ファクトリとfixturesの使用例
└── models/                        # モデルのテスト
    ├── __init__.py
    ├── article_test.py            # Articleモデルのテスト
    └── comment_test.py            # Commentモデルのテスト
```

## テストの実行

### 全てのテストを実行

```bash
pytest
```

### 特定のテストファイルを実行

```bash
pytest app/tests/test_factories_example.py
```

### 特定のテストクラスを実行

```bash
pytest app/tests/test_factories_example.py::TestUserFactory
```

### 特定のテストメソッドを実行

```bash
pytest app/tests/test_factories_example.py::TestUserFactory::test_create_user
```

### 詳細な出力で実行

```bash
pytest -v
```

### カバレッジレポート付きで実行

```bash
pytest --cov=app --cov-report=html
```

## Fixturesの使い方

`conftest.py`で定義されたfixturesをテストで使用できます。

### 基本的なfixturesの使用

```python
import pytest
from app.models import Article

@pytest.mark.django_db
def test_with_user(user):
    """単一のユーザーを使用"""
    assert user.id is not None
    assert user.username

@pytest.mark.django_db
def test_with_article(article):
    """単一の記事を使用"""
    assert article.id is not None
    assert article.title
```

### 複数データのfixturesの使用

```python
@pytest.mark.django_db
def test_with_multiple_users(users):
    """複数のユーザーを使用（3人）"""
    assert len(users) == 3

@pytest.mark.django_db
def test_with_multiple_articles(articles):
    """複数の記事を使用（5件）"""
    assert len(articles) == 5
```

### ファクトリfixturesの使用

```python
@pytest.mark.django_db
def test_with_factory(user_factory, article_factory):
    """ファクトリを使ってカスタムデータを作成"""
    author = user_factory(username='test_author')
    article = article_factory(user=author, title='Test Title')

    assert article.user.username == 'test_author'
    assert article.title == 'Test Title'
```

### コメント付き記事のfixtureの使用

```python
@pytest.mark.django_db
def test_with_article_with_comments(article_with_comments):
    """コメント付きの記事を使用"""
    assert article_with_comments.comments.count() == 3
```

## 利用可能なFixtures

### ユーザー関連
- `user` - 単一のユーザー
- `users` - 複数のユーザー（3人）
- `user_factory` - ユーザーを作成するファクトリ関数

### 記事関連
- `article` - 単一の記事
- `articles` - 複数の記事（5件）
- `article_factory` - 記事を作成するファクトリ関数
- `article_with_comments` - コメント付きの記事

### コメント関連
- `comment` - 単一のコメント
- `comments` - 複数のコメント（3件）
- `comment_factory` - コメントを作成するファクトリ関数

## Factoriesの使い方

`factories.py`で定義されたファクトリクラスを直接使用することもできます。

### UserFactoryの使用

```python
from app.tests.factories import UserFactory

@pytest.mark.django_db
def test_user_creation():
    # デフォルト値でユーザーを作成
    user = UserFactory.create()

    # カスタム値でユーザーを作成
    user = UserFactory.create(username='custom_user', email='custom@example.com')

    # 複数のユーザーを作成
    users = UserFactory.create_batch(size=5)
```

### ArticleFactoryの使用

```python
from app.tests.factories import ArticleFactory, UserFactory

@pytest.mark.django_db
def test_article_creation():
    # デフォルト値で記事を作成（ユーザーも自動生成）
    article = ArticleFactory.create()

    # 特定のユーザーで記事を作成
    user = UserFactory.create()
    article = ArticleFactory.create(user=user, title='Custom Title')

    # 複数の記事を作成
    articles = ArticleFactory.create_batch(size=5)
```

### CommentFactoryの使用

```python
from app.tests.factories import CommentFactory, ArticleFactory

@pytest.mark.django_db
def test_comment_creation():
    # デフォルト値でコメントを作成（記事とユーザーも自動生成）
    comment = CommentFactory.create()

    # 特定の記事にコメントを作成
    article = ArticleFactory.create()
    comment = CommentFactory.create(article=article)

    # 複数のコメントを作成
    comments = CommentFactory.create_batch(size=3, article=article)
```

### ヘルパー関数の使用

```python
from app.tests.factories import create_article_with_comments

@pytest.mark.django_db
def test_article_with_comments():
    # コメント付きの記事を作成（デフォルト3件のコメント）
    article = create_article_with_comments()

    # 指定した数のコメント付き記事を作成
    article = create_article_with_comments(num_comments=10)
```

## Fakerの使い方

日本語のFakerインスタンスを使用してランダムなデータを生成できます。

```python
from faker import Faker

fake = Faker('ja_JP')

# ランダムなテキストデータを生成
name = fake.name()              # 日本語の名前
email = fake.email()            # メールアドレス
text = fake.text()              # ランダムなテキスト
sentence = fake.sentence()      # ランダムな文章
url = fake.url()                # URL
```

## 実際のテスト例

### モデルテストの例

既存のテストファイルを参考にしてください：

- [models/article_test.py](models/article_test.py) - Articleモデルのテスト例
- [models/comment_test.py](models/comment_test.py) - Commentモデルのテスト例
- [test_factories_example.py](test_factories_example.py) - Factoryとfixturesの使用例

### 基本的なテストの書き方

```python
import pytest
from app.models import Article
from app.tests.factories import ArticleFactory

@pytest.mark.django_db
class TestArticle:
    """Articleのテスト"""

    def test_article_creation(self, article):
        """fixtureを使ったテスト"""
        assert article.id is not None
        assert article.title

    def test_article_custom_creation(self):
        """Factoryを直接使ったテスト"""
        article = ArticleFactory.create(title='カスタムタイトル')
        assert article.title == 'カスタムタイトル'

    def test_article_with_factory_fixture(self, article_factory):
        """Factory fixtureを使ったテスト"""
        article = article_factory(title='テスト')
        assert article.title == 'テスト'
```

## ベストプラクティス

1. **@pytest.mark.django_dbを使用**: データベースにアクセスするテストには必ず付ける
2. **Fixturesを活用**: 共通のテストデータは`conftest.py`のfixturesで定義
3. **Factoriesを使う**: テストデータの作成は`factories.py`のFactoryを使用
4. **テストの独立性**: 各テストは独立して実行できるようにする（他のテストに依存しない）
5. **適切な命名**: テストメソッド名は`test_`で始め、何をテストしているか明確にする
6. **クラスでグループ化**: 関連するテストは`TestXxx`クラスでグループ化する
7. **日本語のdocstring**: テストの目的を日本語で明確に記述する

## 参考リンク

- [pytest-django Documentation](https://pytest-django.readthedocs.io/)
- [model-bakery Documentation](https://model-bakery.readthedocs.io/)
- [Faker Documentation](https://faker.readthedocs.io/)
