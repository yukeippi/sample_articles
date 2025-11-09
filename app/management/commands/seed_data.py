from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Article, Comment


class Command(BaseCommand):
    help = '初期データを投入するコマンド'

    def add_arguments(self, parser):
        # オプション引数を追加できます
        parser.add_argument(
            '--clear',
            action='store_true',
            help='既存のデータを削除してから投入',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('既存のデータを削除しています...')
            Comment.objects.all().delete()
            Article.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        self.stdout.write('初期データを投入しています...')

        # サンプルユーザーを作成
        users = []
        for username in ['太郎', '花子', '次郎']:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                }
            )
            users.append(user)

        # サンプル記事を作成
        articles = [
            Article(
                title='Djangoの始め方',
                content='Djangoは強力なPython製のWebフレームワークです。モデル、ビュー、テンプレートの3層構造で構成されています。',
                user=users[0],
            ),
            Article(
                title='Pythonのベストプラクティス',
                content='Pythonでコードを書く際のベストプラクティスを紹介します。PEP 8に従い、読みやすいコードを心がけましょう。',
                user=users[1],
            ),
            Article(
                title='Web開発の基礎',
                content='Web開発の基礎について学びます。HTTP、REST API、データベースなどの重要な概念を理解しましょう。',
                user=users[2],
            ),
        ]

        Article.objects.bulk_create(articles)
        created_articles = list(Article.objects.all().order_by('-created_at'))

        # サンプルコメントを作成
        comments = [
            Comment(
                article=created_articles[0],
                user=users[1],
                content='とても参考になりました！',
            ),
            Comment(
                article=created_articles[0],
                user=users[2],
                content='わかりやすい説明ですね。',
            ),
            Comment(
                article=created_articles[1],
                user=users[0],
                content='ありがとうございます。勉強になります。',
            ),
            Comment(
                article=created_articles[1],
                user=users[2],
                content='実践的な内容で助かります。',
            ),
        ]

        Comment.objects.bulk_create(comments)

        self.stdout.write(
            self.style.SUCCESS(
                f'初期データの投入が完了しました。'
                f'ユーザー: {User.objects.count()}件, '
                f'記事: {Article.objects.count()}件, '
                f'コメント: {Comment.objects.count()}件'
            )
        )
