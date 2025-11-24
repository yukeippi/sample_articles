from uuid import uuid7

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .base import TimestampedModel


class UpdateStatus(models.Model):
    """更新ステータスマスター"""

    PENDING = 'pending'  # 予約中
    APPLIED = 'applied'  # 適用済み
    CANCELLED = 'cancelled'  # キャンセル済み

    STATUS_CHOICES = [
        (PENDING, '予約中'),
        (APPLIED, '適用済み'),
        (CANCELLED, 'キャンセル済み'),
    ]

    code = models.CharField(max_length=20, primary_key=True, verbose_name='ステータスコード')
    name = models.CharField(max_length=50, verbose_name='ステータス名')

    class Meta:
        verbose_name = '更新ステータス'
        verbose_name_plural = '更新ステータス'

    def __str__(self):
        return self.name


class Reservation(TimestampedModel):
    """汎用予約更新データ"""

    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'

    ACTION_CHOICES = [
        (ACTION_CREATE, '新規作成'),
        (ACTION_UPDATE, '更新'),
        (ACTION_DELETE, '削除'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name='ID')

    # 対象モデルの指定（GenericForeignKey）
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='対象モデル',
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name='対象オブジェクトID',
        help_text='新規作成の場合はNull',
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    # 操作内容
    action = models.CharField(
        max_length=10,
        choices=ACTION_CHOICES,
        verbose_name='操作種別',
    )

    # 更新内容（JSONB）
    data = models.JSONField(
        verbose_name='更新データ',
        help_text='更新する内容をJSON形式で保存',
    )

    # 依存する予約更新（親が未作成の予約更新の場合など）
    depends_on = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='dependents',
        verbose_name='依存予約（親として使用）',
        help_text='未適用の予約を親として指定する場合に設定',
    )

    # スケジュール
    scheduled_date = models.DateField(verbose_name='適用予定日')

    # ステータス
    status = models.ForeignKey(
        UpdateStatus,
        on_delete=models.PROTECT,
        default=UpdateStatus.PENDING,
        verbose_name='ステータス',
    )

    # 適用結果
    applied_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='適用日時',
    )
    applied_object_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name='適用後オブジェクトID',
        help_text='新規作成時に生成されたオブジェクトのID',
    )

    class Meta:
        verbose_name = '予約更新'
        verbose_name_plural = '予約更新'
        ordering = ['scheduled_date', 'created_at']
        indexes = [
            models.Index(fields=['scheduled_date', 'status']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['depends_on']),
        ]

    def __str__(self):
        model_name = self.content_type.model if self.content_type else 'Unknown'
        target = self.content_object or self.data.get('name', 'Unknown')
        return f'{model_name}: {self.get_action_display()} - {target} ({self.scheduled_date})'

    def get_display_name(self):
        """表示名を取得"""
        if self.action == self.ACTION_CREATE:
            return self.data.get('name', '新規')
        elif self.content_object:
            return str(self.content_object)
        else:
            return f"ID: {self.object_id}"

    def check_circular_dependency(self):
        """循環参照チェック

        Returns:
            bool: 循環参照がない場合True、ある場合False

        Raises:
            ValueError: 循環参照が検出された場合
        """
        visited = set()
        current = self.depends_on

        while current:
            if current.id in visited:
                # 循環参照を検出
                raise ValueError(
                    f'循環参照が検出されました: {self.id} -> ... -> {current.id}'
                )
            visited.add(current.id)
            current = current.depends_on

        return True

    @staticmethod
    def topological_sort(reservations):
        """トポロジカルソートで予約更新の適用順序を決定

        Args:
            reservations: QuerySetまたは予約更新のリスト

        Returns:
            list: 適用順序に並び替えられた予約更新のリスト

        Raises:
            ValueError: 循環参照が検出された場合
        """
        # 予約更新をリストに変換
        reservation_list = list(reservations)

        # IDでインデックス化
        reservation_dict = {r.id: r for r in reservation_list}

        # 依存グラフを構築（被依存 -> 依存のマッピング）
        dependents = {r.id: [] for r in reservation_list}
        in_degree = {r.id: 0 for r in reservation_list}

        for reservation in reservation_list:
            if reservation.depends_on and reservation.depends_on.id in reservation_dict:
                # depends_on -> reservation の依存関係
                dependents[reservation.depends_on.id].append(reservation.id)
                in_degree[reservation.id] += 1

        # Kahn's algorithm でトポロジカルソート
        queue = [r.id for r in reservation_list if in_degree[r.id] == 0]
        sorted_ids = []

        while queue:
            # 予定日が早い順、作成日時が早い順にソート
            queue.sort(key=lambda rid: (
                reservation_dict[rid].scheduled_date,
                reservation_dict[rid].created_at
            ))

            current_id = queue.pop(0)
            sorted_ids.append(current_id)

            # 依存している予約更新の入次数を減らす
            for dependent_id in dependents[current_id]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        # 全ての予約更新がソートされたか確認（循環参照チェック）
        if len(sorted_ids) != len(reservation_list):
            raise ValueError('循環参照が検出されました。依存関係を確認してください。')

        # ソート順に予約更新オブジェクトを並べて返す
        return [reservation_dict[rid] for rid in sorted_ids]
