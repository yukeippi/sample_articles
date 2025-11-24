from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from app.models import OrganizationReservation, UpdateStatus


class Command(BaseCommand):
    help = '予約更新を適用するバッチコマンド'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='適用日を指定 (YYYY-MM-DD形式、未指定の場合は今日)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際には適用せず、適用対象のみ表示',
        )

    def handle(self, *args, **options):
        # 適用日を取得
        target_date_str = options.get('date')
        if target_date_str:
            try:
                target_date = date.fromisoformat(target_date_str)
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f'日付フォーマットが不正です: {target_date_str}')
                )
                return
        else:
            target_date = date.today()

        self.stdout.write(f'適用対象日: {target_date}')

        # 適用対象の予約更新を取得
        reservations = OrganizationReservation.objects.filter(
            scheduled_date__lte=target_date, status_id=UpdateStatus.PENDING
        ).select_related('organization', 'parent').order_by('scheduled_date', 'created_at')

        if not reservations.exists():
            self.stdout.write(self.style.WARNING('適用対象の予約更新がありません'))
            return

        self.stdout.write(f'適用対象: {reservations.count()}件')

        # Dry-runモード
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('--- Dry-run モード ---'))
            for reservation in reservations:
                self.stdout.write(
                    f'  - [{reservation.get_action_display()}] '
                    f'{reservation.name or reservation.organization} '
                    f'(予定日: {reservation.scheduled_date})'
                )
            return

        # トランザクション内で適用
        success_count = 0
        error_count = 0

        with transaction.atomic():
            for reservation in reservations:
                try:
                    reservation.apply()
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ 適用完了: [{reservation.get_action_display()}] '
                            f'{reservation.name or reservation.organization}'
                        )
                    )
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ 適用失敗: [{reservation.get_action_display()}] '
                            f'{reservation.name or reservation.organization} - {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(f'\n処理完了: 成功 {success_count}件 / 失敗 {error_count}件')
        )
