"""組織予約更新のヘルパー"""

from uuid import uuid7

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from app.models import Organization, Reservation, UpdateStatus


class OrganizationReservationHelper:
    """組織予約更新のヘルパークラス"""

    @staticmethod
    def get_content_type():
        """組織のContentTypeを取得"""
        return ContentType.objects.get_for_model(Organization)

    @staticmethod
    def validate_hierarchy(organization_id, parent_id):
        """組織階層の妥当性を検証

        Args:
            organization_id: 対象組織のID（新規作成の場合はNone）
            parent_id: 親組織のID

        Raises:
            ValueError: 階層が不正な場合
        """
        if not parent_id:
            return  # 親なし（ルート組織）は常に有効

        if organization_id and str(organization_id) == str(parent_id):
            raise ValueError('組織は自分自身を親にできません')

        # 親組織が存在し、その子孫に対象組織が含まれていないか確認
        if organization_id:
            try:
                org = Organization.objects.get(id=organization_id)
                parent = Organization.objects.get(id=parent_id)

                # 親組織の先祖に対象組織が含まれていないか確認
                ancestors = parent.get_ancestors()
                if org in ancestors:
                    raise ValueError('循環参照になる親組織は指定できません')
            except Organization.DoesNotExist:
                pass  # 新規作成の場合はチェック不要

    @staticmethod
    def create_reservation(action, scheduled_date, organization=None, name=None, parent=None, parent_reservation=None):
        """組織の予約更新を作成

        Args:
            action: 操作種別 ('create', 'update', 'delete')
            scheduled_date: 適用予定日
            organization: 対象組織（新規作成の場合はNone）
            name: 組織名（新規作成/更新の場合）
            parent: 親組織（既存の組織）
            parent_reservation: 親組織（未来の予約更新）

        Raises:
            ValueError: 階層が不正な場合、または循環参照が検出された場合
        """
        content_type = OrganizationReservationHelper.get_content_type()

        # 階層検証（既存の親組織が指定されている場合）
        if parent:
            OrganizationReservationHelper.validate_hierarchy(
                organization_id=organization.id if organization else None,
                parent_id=parent.id
            )

        data = {}
        if name:
            data['name'] = name
        if parent:
            data['parent_id'] = str(parent.id)
        elif parent is None and action in [Reservation.ACTION_CREATE, Reservation.ACTION_UPDATE]:
            # 親をNullに設定する場合（ルート組織にする）
            data['parent_id'] = None

        # parent_reservationが指定されている場合は、depends_onに設定
        depends_on = parent_reservation if parent_reservation else None

        reservation = Reservation.objects.create(
            content_type=content_type,
            object_id=organization.id if organization else None,
            action=action,
            data=data,
            scheduled_date=scheduled_date,
            depends_on=depends_on,
            status_id=UpdateStatus.PENDING,
        )

        # 循環参照チェック
        try:
            reservation.check_circular_dependency()
        except ValueError as e:
            # 循環参照が検出された場合は作成した予約を削除
            reservation.delete()
            raise e

        return reservation

    @staticmethod
    def apply_reservation(reservation):
        """予約更新を適用

        Args:
            reservation: Reservationオブジェクト

        Returns:
            適用後のOrganizationオブジェクト
        """
        if reservation.status_id != UpdateStatus.PENDING:
            raise ValueError('適用できるのは予約中のレコードのみです')

        if reservation.content_type != OrganizationReservationHelper.get_content_type():
            raise ValueError('組織以外の予約更新は適用できません')

        with transaction.atomic():
            if reservation.action == Reservation.ACTION_CREATE:
                # 新規作成
                parent_id = reservation.data.get('parent_id')
                parent = None

                # 既存の親組織が指定されている場合
                if parent_id:
                    parent = Organization.objects.get(id=parent_id)
                # depends_onで未来の組織が親として指定されている場合
                elif reservation.depends_on and reservation.depends_on.applied_object_id:
                    parent = Organization.objects.get(id=reservation.depends_on.applied_object_id)

                org = Organization.objects.create(
                    id=uuid7(),
                    name=reservation.data['name'],
                    parent=parent,
                )
                reservation.applied_object_id = org.id

            elif reservation.action == Reservation.ACTION_UPDATE:
                # 更新
                if not reservation.object_id:
                    raise ValueError('更新対象の組織が指定されていません')

                org = Organization.objects.get(id=reservation.object_id)

                if 'name' in reservation.data:
                    org.name = reservation.data['name']

                if 'parent_id' in reservation.data:
                    parent_id = reservation.data['parent_id']
                    parent = None
                    if parent_id:
                        parent = Organization.objects.get(id=parent_id)
                    # depends_onで未来の組織が親として指定されている場合
                    elif reservation.depends_on and reservation.depends_on.applied_object_id:
                        parent = Organization.objects.get(id=reservation.depends_on.applied_object_id)
                    org.parent = parent

                org.save()

            elif reservation.action == Reservation.ACTION_DELETE:
                # 削除
                if not reservation.object_id:
                    raise ValueError('削除対象の組織が指定されていません')

                org = Organization.objects.get(id=reservation.object_id)
                org.delete()

            # ステータスを適用済みに変更
            reservation.status_id = UpdateStatus.APPLIED
            reservation.applied_at = timezone.now()
            reservation.save()

            return org if reservation.action != Reservation.ACTION_DELETE else None

    @staticmethod
    def get_pending_reservations(scheduled_date=None):
        """予約中の組織予約更新を取得

        Args:
            scheduled_date: 指定日以前の予約のみ取得（Noneの場合は全て）
        """
        content_type = OrganizationReservationHelper.get_content_type()
        queryset = Reservation.objects.filter(
            content_type=content_type,
            status_id=UpdateStatus.PENDING,
        )

        if scheduled_date:
            queryset = queryset.filter(scheduled_date__lte=scheduled_date)

        return queryset.order_by('scheduled_date', 'created_at')

    @staticmethod
    def format_for_display(reservation):
        """予約更新を表示用にフォーマット

        Returns:
            dict: {
                'id': UUID,
                'action': str,
                'action_display': str,
                'organization': Organization or None,
                'name': str,
                'parent': Organization or None,
                'scheduled_date': date,
                'status': str,
            }
        """
        organization = None
        if reservation.object_id:
            try:
                organization = Organization.objects.get(id=reservation.object_id)
            except Organization.DoesNotExist:
                pass

        parent = None
        parent_id = reservation.data.get('parent_id')
        if parent_id:
            try:
                parent = Organization.objects.get(id=parent_id)
            except Organization.DoesNotExist:
                pass

        return {
            'id': reservation.id,
            'action': reservation.action,
            'action_display': reservation.get_action_display(),
            'organization': organization,
            'name': reservation.data.get('name'),
            'parent': parent,
            'scheduled_date': reservation.scheduled_date,
            'status': reservation.status,
            'depends_on': reservation.depends_on,
        }
