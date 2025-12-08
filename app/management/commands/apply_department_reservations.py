from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from app.models import Reservation, UpdateStatus
from app.utils.department_reservation import DepartmentReservationHelper


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
        reservations = DepartmentReservationHelper.get_pending_reservations(
            scheduled_date=target_date
        )

        if not reservations.exists():
            self.stdout.write(self.style.WARNING('適用対象の予約更新がありません'))
            return

        self.stdout.write(f'適用対象: {reservations.count()}件')

        # トポロジカルソートで適用順序を決定
        try:
            sorted_reservations = Reservation.topological_sort(reservations)
            self.stdout.write(self.style.SUCCESS('依存関係を解決しました'))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f'エラー: {str(e)}'))
            return

        # Dry-runモード
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('--- Dry-run モード ---'))
            for idx, reservation in enumerate(sorted_reservations, 1):
                formatted = DepartmentReservationHelper.format_for_display(reservation)
                depends_info = ''
                if reservation.depends_on:
                    depends_info = f' (依存: {reservation.depends_on.data.get("name", "不明")})'
                self.stdout.write(
                    f'  {idx}. [{formatted["action_display"]}] '
                    f'{formatted["name"] or formatted["department"]} '
                    f'(予定日: {formatted["scheduled_date"]}){depends_info}'
                )
            return

        # トランザクション内で適用
        success_count = 0
        error_count = 0

        with transaction.atomic():
            for idx, reservation in enumerate(sorted_reservations, 1):
                try:
                    DepartmentReservationHelper.apply_reservation(reservation)
                    formatted = DepartmentReservationHelper.format_for_display(reservation)
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ [{idx}/{len(sorted_reservations)}] 適用完了: [{formatted["action_display"]}] '
                            f'{formatted["name"] or formatted["department"]}'
                        )
                    )
                except Exception as e:
                    error_count += 1
                    formatted = DepartmentReservationHelper.format_for_display(reservation)
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ [{idx}/{len(sorted_reservations)}] 適用失敗: [{formatted["action_display"]}] '
                            f'{formatted["name"] or formatted["department"]} - {str(e)}'
                        )
                    )
                    # エラーが発生した場合はロールバックのため処理を中断
                    raise

        self.stdout.write(
            self.style.SUCCESS(f'\n処理完了: 成功 {success_count}件 / 失敗 {error_count}件')
        )
