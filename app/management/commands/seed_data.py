from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from faker import Faker
from model_bakery import baker

from app.models import Article, Comment, Employee, Organization

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
        parser.add_argument(
            '--organizations',
            type=int,
            default=10,
            help='作成する組織数（デフォルト: 10）',
        )
        parser.add_argument(
            '--employees',
            type=int,
            default=30,
            help='作成する社員数（デフォルト: 30）',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('既存のデータを削除しています...')
            Comment.objects.all().delete()
            Article.objects.all().delete()
            Employee.objects.all().delete()
            Organization.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        num_users = options['users']
        num_articles = options['articles']
        num_comments = options['comments']
        num_organizations = options['organizations']
        num_employees = options['employees']

        self.stdout.write('初期データを投入しています...')

        # サンプル組織を作成
        self.stdout.write(f'{num_organizations}件の組織を作成しています...')
        organizations = []

        # ルート組織を作成
        root_orgs_count = max(2, num_organizations // 5)
        for _ in range(root_orgs_count):
            org = Organization.objects.create(
                name=fake.company(),
                parent=None,
            )
            organizations.append(org)

        # 子組織を作成
        remaining_orgs = num_organizations - root_orgs_count
        for _ in range(remaining_orgs):
            parent_org = fake.random_element(organizations)
            org = Organization.objects.create(
                name=f'{fake.company()} {fake.random_element(["部", "課", "チーム", "グループ"])}',
                parent=parent_org,
            )
            organizations.append(org)

        # サンプルユーザーを作成
        self.stdout.write(f'{num_users}人のユーザーを作成しています...')
        users = []
        for _ in range(num_users):
            user = baker.make(
                User,
                username=fake.user_name(),
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            user.set_password('password')  # パスワードを「password」に統一
            user.save()
            users.append(user)

        # サンプル社員を作成
        self.stdout.write(f'{num_employees}件の社員を作成しています...')
        employees = []
        for _ in range(num_employees):
            # 70%の確率で組織に所属、30%の確率で未所属
            organization = fake.random_element(organizations) if fake.boolean(chance_of_getting_true=70) else None
            employee = Employee.objects.create(
                name=fake.name(),
                email=fake.email(),
                organization=organization,
            )
            employees.append(employee)

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
                f'  組織: {Organization.objects.count()}件\n'
                f'  社員: {Employee.objects.count()}件\n'
                f'  ユーザー: {User.objects.count()}件\n'
                f'  記事: {Article.objects.count()}件\n'
                f'  コメント: {Comment.objects.count()}件'
            )
        )
