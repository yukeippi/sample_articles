from uuid import uuid7

from django.db import models

from .base import TimestampedModel


class Organization(TimestampedModel):
    """組織マスターモデル（隣接リストモデル）"""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name='ID')
    name = models.CharField(max_length=200, verbose_name='組織名')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='親組織',
    )

    class Meta:
        verbose_name = '組織'
        verbose_name_plural = '組織'
        ordering = ['name']
        indexes = [
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return self.name

    def get_ancestors(self):
        """先祖組織を取得（ルートまで）"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """子孫組織を取得（再帰的に全て）"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_level(self):
        """階層レベルを取得（ルート=0）"""
        return len(self.get_ancestors())


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


class OrganizationReservation(TimestampedModel):
    """組織予約更新データ"""

    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'

    ACTION_CHOICES = [
        (ACTION_CREATE, '新規作成'),
        (ACTION_UPDATE, '更新'),
        (ACTION_DELETE, '削除'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name='ID')
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reservations',
        verbose_name='対象組織',
        help_text='新規作成の場合はNull',
    )
    action = models.CharField(
        max_length=10, choices=ACTION_CHOICES, verbose_name='操作種別'
    )
    name = models.CharField(
        max_length=200, null=True, blank=True, verbose_name='組織名'
    )
    parent = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_reservations',
        verbose_name='親組織',
    )
    scheduled_date = models.DateField(verbose_name='適用予定日')
    status = models.ForeignKey(
        UpdateStatus,
        on_delete=models.PROTECT,
        default=UpdateStatus.PENDING,
        verbose_name='ステータス',
    )

    class Meta:
        verbose_name = '組織予約更新'
        verbose_name_plural = '組織予約更新'
        ordering = ['scheduled_date', 'created_at']
        indexes = [
            models.Index(fields=['scheduled_date', 'status']),
            models.Index(fields=['organization']),
        ]

    def __str__(self):
        return f'{self.get_action_display()} - {self.name or self.organization} ({self.scheduled_date})'

    def apply(self):
        """予約を適用する"""
        if self.status_id != UpdateStatus.PENDING:
            raise ValueError('適用できるのは予約中のレコードのみです')

        if self.action == self.ACTION_CREATE:
            # 新規作成
            org = Organization.objects.create(
                id=uuid7(),
                name=self.name,
                parent=self.parent,
            )
            self.organization = org
        elif self.action == self.ACTION_UPDATE:
            # 更新
            if not self.organization:
                raise ValueError('更新対象の組織が指定されていません')
            if self.name:
                self.organization.name = self.name
            if self.parent is not None:
                self.organization.parent = self.parent
            self.organization.save()
        elif self.action == self.ACTION_DELETE:
            # 削除
            if not self.organization:
                raise ValueError('削除対象の組織が指定されていません')
            self.organization.delete()

        # ステータスを適用済みに変更
        self.status_id = UpdateStatus.APPLIED
        self.save()
