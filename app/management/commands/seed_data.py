from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from faker import Faker
from model_bakery import baker

from app.models import Article, Comment

fake = Faker('ja_JP')


class Command(BaseCommand):
    help = '初期データを投入するコマンド'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='既存のデータを削除してから投入',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='作成するユーザー数（デフォルト: 5）',
        )
        parser.add_argument(
            '--articles',
            type=int,
            default=10,
            help='作成する記事数（デフォルト: 10）',
        )
        parser.add_argument(
            '--comments',
            type=int,
            default=20,
            help='作成するコメント数（デフォルト: 20）',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('既存のデータを削除しています...')
            Comment.objects.all().delete()
            Article.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        num_users = options['users']
        num_articles = options['articles']
        num_comments = options['comments']

        self.stdout.write('初期データを投入しています...')

        # サンプルユーザーを作成
        self.stdout.write(f'{num_users}人のユーザーを作成しています...')
        users = baker.make(
            User,
            num_users,
            username=fake.user_name,
            email=fake.email,
            first_name=fake.first_name,
            last_name=fake.last_name,
        )

        # サンプル記事を作成
        self.stdout.write(f'{num_articles}件の記事を作成しています...')
        articles = baker.make(
            Article,
            num_articles,
            title=lambda: fake.sentence(nb_words=6)[:-1],  # 最後のピリオドを削除
            content=lambda: fake.text(max_nb_chars=500),
            user=lambda: fake.random_element(users),
        )

        # サンプルコメントを作成
        self.stdout.write(f'{num_comments}件のコメントを作成しています...')
        baker.make(
            Comment,
            num_comments,
            article=lambda: fake.random_element(articles),
            user=lambda: fake.random_element(users),
            content=lambda: fake.text(max_nb_chars=200),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'初期データの投入が完了しました。\n'
                f'  ユーザー: {User.objects.count()}件\n'
                f'  記事: {Article.objects.count()}件\n'
                f'  コメント: {Comment.objects.count()}件'
            )
        )
