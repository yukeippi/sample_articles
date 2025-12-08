"""社員予約更新のヘルパー"""

from uuid import uuid7

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from app.models import Employee, Reservation, UpdateStatus


class EmployeeReservationHelper:
    """社員予約更新のヘルパークラス"""

    @staticmethod
    def get_content_type():
        """社員のContentTypeを取得"""
        return ContentType.objects.get_for_model(Employee)

    @staticmethod
    def create_reservation(action, scheduled_date, employee=None, name=None, email=None, department=None):
        """社員の予約更新を作成

        Args:
            action: 操作種別 ('create', 'update', 'delete')
            scheduled_date: 適用予定日
            employee: 対象社員（新規作成の場合はNone）
            name: 氏名（新規作成/更新の場合）
            email: メールアドレス（新規作成/更新の場合）
            department: 所属組織

        Raises:
            ValueError: 入力が不正な場合
        """
        content_type = EmployeeReservationHelper.get_content_type()

        data = {}
        if name:
            data['name'] = name
        if email:
            data['email'] = email
        if department:
            data['department_id'] = str(department.id)
        elif department is None and action in [Reservation.ACTION_CREATE, Reservation.ACTION_UPDATE]:
            # 組織をNullに設定する場合
            data['department_id'] = None

        reservation = Reservation.objects.create(
            content_type=content_type,
            object_id=employee.id if employee else None,
            action=action,
            data=data,
            scheduled_date=scheduled_date,
            status_id=UpdateStatus.PENDING,
        )

        return reservation

    @staticmethod
    def apply_reservation(reservation):
        """予約更新を適用

        Args:
            reservation: Reservationオブジェクト

        Returns:
            適用後のEmployeeオブジェクト
        """
        if reservation.status_id != UpdateStatus.PENDING:
            raise ValueError('適用できるのは予約中のレコードのみです')

        if reservation.content_type != EmployeeReservationHelper.get_content_type():
            raise ValueError('社員以外の予約更新は適用できません')

        with transaction.atomic():
            if reservation.action == Reservation.ACTION_CREATE:
                # 新規作成
                department_id = reservation.data.get('department_id')
                department = None
                if department_id:
                    from app.models import Department
                    department = Department.objects.get(id=department_id)

                employee = Employee.objects.create(
                    id=uuid7(),
                    name=reservation.data['name'],
                    email=reservation.data['email'],
                    department=department,
                )
                reservation.applied_object_id = employee.id

            elif reservation.action == Reservation.ACTION_UPDATE:
                # 更新
                if not reservation.object_id:
                    raise ValueError('更新対象の社員が指定されていません')

                employee = Employee.objects.get(id=reservation.object_id)

                if 'name' in reservation.data:
                    employee.name = reservation.data['name']

                if 'email' in reservation.data:
                    employee.email = reservation.data['email']

                if 'department_id' in reservation.data:
                    department_id = reservation.data['department_id']
                    if department_id:
                        from app.models import Department
                        employee.department = Department.objects.get(id=department_id)
                    else:
                        employee.department = None

                employee.save()

            elif reservation.action == Reservation.ACTION_DELETE:
                # 削除
                if not reservation.object_id:
                    raise ValueError('削除対象の社員が指定されていません')

                employee = Employee.objects.get(id=reservation.object_id)
                employee.delete()

            # ステータスを適用済みに変更
            reservation.status_id = UpdateStatus.APPLIED
            reservation.applied_at = timezone.now()
            reservation.save()

            return employee if reservation.action != Reservation.ACTION_DELETE else None

    @staticmethod
    def get_pending_reservations(scheduled_date=None):
        """予約中の社員予約更新を取得

        Args:
            scheduled_date: 指定日以前の予約のみ取得（Noneの場合は全て）
        """
        content_type = EmployeeReservationHelper.get_content_type()
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
                'employee': Employee or None,
                'name': str,
                'email': str,
                'department': Department or None,
                'scheduled_date': date,
                'status': str,
            }
        """
        employee = None
        if reservation.object_id:
            try:
                employee = Employee.objects.get(id=reservation.object_id)
            except Employee.DoesNotExist:
                pass

        department = None
        department_id = reservation.data.get('department_id')
        if department_id:
            try:
                from app.models import Department
                department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                pass

        return {
            'id': reservation.id,
            'action': reservation.action,
            'action_display': reservation.get_action_display(),
            'employee': employee,
            'name': reservation.data.get('name'),
            'email': reservation.data.get('email'),
            'department': department,
            'scheduled_date': reservation.scheduled_date,
            'status': reservation.status,
        }
