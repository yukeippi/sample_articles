from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'データベースをリセット（削除、作成、マイグレーション）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='確認なしで実行',
        )
        parser.add_argument(
            '--seed',
            action='store_true',
            help='リセット後に初期データを投入',
        )

    def handle(self, *args, **options):
        db_name = settings.DATABASES['default']['NAME']

        # 確認
        if not options['noinput']:
            confirm = input(
                f'データベース "{db_name}" を削除して再作成します。よろしいですか？ [y/N]: '
            )
            if confirm.lower() != 'y':
                self.stdout.write('キャンセルしました。')
                return

        # 既存の接続を閉じる
        connection.close()

        self.stdout.write('全テーブルを削除しています...')

        # django-extensionsのreset_dbコマンドを使用
        try:
            call_command('reset_db', '--noinput', '--close-sessions')
            self.stdout.write(self.style.SUCCESS('削除完了'))
        except Exception:
            # django-extensionsが使えない場合は、flushを使用
            self.stdout.write(
                self.style.WARNING('reset_dbコマンドが使用できません。flushを使用します。')
            )
            try:
                call_command('flush', '--noinput')
                self.stdout.write(self.style.SUCCESS('データ削除完了'))
            except Exception as flush_error:
                raise CommandError(
                    f'データベースのリセットに失敗しました: {flush_error}'
                ) from flush_error

        # マイグレーションを実行
        self.stdout.write('マイグレーションを実行しています...')
        call_command('migrate', interactive=False)
        self.stdout.write(self.style.SUCCESS('マイグレーション完了'))

        # 初期データを投入
        if options['seed']:
            self.stdout.write('初期データを投入しています...')
            call_command('seed_data')

        self.stdout.write(self.style.SUCCESS('データベースのリセットが完了しました！'))
