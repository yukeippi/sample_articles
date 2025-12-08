"""
社員モデルのテスト
"""

import pytest
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError

from app.models import Employee, Department
from app.tests.factories import (
    EmployeeFactory,
    DepartmentFactory,
    create_department_with_employees,
)


@pytest.mark.django_db
class TestEmployeeModel:
    """社員モデルのテスト"""

    def test_create_employee_with_department(self):
        """組織に所属する社員の作成"""
        org = DepartmentFactory.create(name='営業部')
        employee = EmployeeFactory.create(
            name='山田太郎',
            email='yamada@example.com',
            department=org,
        )

        assert employee.name == '山田太郎'
        assert employee.email == 'yamada@example.com'
        assert employee.department == org
        assert employee in org.employees.all()

    def test_create_employee_without_department(self):
        """未所属社員の作成"""
        employee = EmployeeFactory.create(
            name='田中花子',
            email='tanaka@example.com',
            department=None,
        )

        assert employee.name == '田中花子'
        assert employee.department is None

    def test_str_representation(self):
        """文字列表現"""
        employee = EmployeeFactory.create(name='山田太郎', email='yamada@example.com')
        assert str(employee) == '山田太郎 (yamada@example.com)'

    def test_email_uniqueness_validation(self):
        """メールアドレスの重複チェック（有効な社員のみ）"""
        email = 'yamada@example.com'
        EmployeeFactory.create(email=email)

        # 同じメールアドレスで作成しようとするとValidationError
        with pytest.raises(ValidationError) as excinfo:
            EmployeeFactory.create(email=email)

        assert 'email' in excinfo.value.message_dict

    def test_email_uniqueness_allows_deleted(self):
        """論理削除された社員のメールアドレスは再利用可能"""
        email = 'yamada@example.com'
        employee1 = EmployeeFactory.create(name='山田太郎', email=email)

        # 論理削除
        employee1.delete()

        # 同じメールアドレスで新しい社員を作成可能
        employee2 = EmployeeFactory.create(name='山田次郎', email=email)

        assert employee2.email == email
        assert employee1.id != employee2.id

    def test_update_employee(self):
        """社員情報の更新"""
        employee = EmployeeFactory.create(name='山田太郎')
        new_name = '山田次郎'

        employee.name = new_name
        employee.save()

        employee.refresh_from_db()
        assert employee.name == new_name


@pytest.mark.django_db
class TestEmployeeSoftDelete:
    """社員の論理削除のテスト"""

    def test_soft_delete(self):
        """論理削除"""
        employee = EmployeeFactory.create()
        employee_id = employee.id

        # 論理削除を実行
        employee.delete()

        # デフォルトのマネージャーでは取得できない
        assert not Employee.objects.filter(id=employee_id).exists()

        # with_deleted() で取得可能
        deleted_employee = Employee.objects.with_deleted().get(id=employee_id)
        assert deleted_employee.is_deleted
        assert deleted_employee.deleted_at is not None

    def test_restore(self):
        """論理削除の復元"""
        employee = EmployeeFactory.create()

        # 論理削除
        employee.delete()
        assert employee.is_deleted

        # 復元
        employee.restore()
        assert not employee.is_deleted
        assert employee.deleted_at is None

        # デフォルトのマネージャーで取得可能
        assert Employee.objects.filter(id=employee.id).exists()

    def test_hard_delete(self):
        """物理削除"""
        employee = EmployeeFactory.create()
        employee_id = employee.id

        # 物理削除
        employee.hard_delete()

        # どのマネージャーでも取得不可
        assert not Employee.objects.with_deleted().filter(id=employee_id).exists()
        assert not Employee.all_objects.filter(id=employee_id).exists()


@pytest.mark.django_db
class TestEmployeeDepartmentRelationship:
    """社員と組織の関連のテスト"""

    def test_department_soft_delete_sets_employee_department_to_null(self):
        """組織の論理削除時に社員の組織がNULLになる"""
        org, employees = create_department_with_employees(num_employees=3)

        # 組織を論理削除
        org.delete()

        # 社員の組織がNULLになる
        for employee in employees:
            employee.refresh_from_db()
            assert employee.department is None

    def test_employee_can_be_transferred_to_another_department(self):
        """社員を他の組織に異動できる"""
        org1 = DepartmentFactory.create(name='営業部')
        org2 = DepartmentFactory.create(name='開発部')
        employee = EmployeeFactory.create(department=org1)

        # 異動
        employee.department = org2
        employee.save()

        employee.refresh_from_db()
        assert employee.department == org2
        assert employee in org2.employees.all()
        assert employee not in org1.employees.all()

    def test_employee_can_be_unaffiliated(self):
        """社員を未所属にできる"""
        org = DepartmentFactory.create(name='営業部')
        employee = EmployeeFactory.create(department=org)

        # 未所属化
        employee.department = None
        employee.save()

        employee.refresh_from_db()
        assert employee.department is None

    def test_query_unaffiliated_employees(self):
        """未所属社員の取得"""
        org = DepartmentFactory.create(name='営業部')
        employee1 = EmployeeFactory.create(department=org)
        employee2 = EmployeeFactory.create(department=None)
        employee3 = EmployeeFactory.create(department=None)

        # 未所属社員を取得
        unaffiliated = Employee.objects.filter(department__isnull=True)

        assert employee2 in unaffiliated
        assert employee3 in unaffiliated
        assert employee1 not in unaffiliated

    def test_query_affiliated_employees(self):
        """所属社員の取得"""
        org = DepartmentFactory.create(name='営業部')
        employee1 = EmployeeFactory.create(department=org)
        employee2 = EmployeeFactory.create(department=None)

        # 所属社員を取得
        affiliated = Employee.objects.filter(department__isnull=False)

        assert employee1 in affiliated
        assert employee2 not in affiliated

    def test_department_hard_delete_protected_by_employees(self):
        """社員が存在する組織は物理削除できない（PROTECT制約）"""
        org = DepartmentFactory.create(name='営業部')
        EmployeeFactory.create(department=org)

        # 物理削除しようとするとProtectedError
        with pytest.raises(ProtectedError):
            org.hard_delete()

    def test_department_hard_delete_after_moving_employees(self):
        """社員を移動後に組織を物理削除できる"""
        org1 = DepartmentFactory.create(name='営業部')
        org2 = DepartmentFactory.create(name='開発部')
        employee = EmployeeFactory.create(department=org1)

        # 社員を別の組織に移動
        employee.department = org2
        employee.save()

        # 組織を物理削除できる
        org1.hard_delete()

        # 社員は別の組織に所属している
        employee.refresh_from_db()
        assert employee.department == org2

    def test_department_hard_delete_after_setting_employees_to_null(self):
        """社員を未所属化後に組織を物理削除できる"""
        org = DepartmentFactory.create(name='営業部')
        employee = EmployeeFactory.create(department=org)

        # 社員を未所属化
        employee.department = None
        employee.save()

        # 組織を物理削除できる
        org.hard_delete()

        # 社員は未所属のまま
        employee.refresh_from_db()
        assert employee.department is None


@pytest.mark.django_db
class TestEmployeeQueries:
    """社員のクエリのテスト"""

    def test_default_manager_excludes_deleted(self):
        """デフォルトマネージャーは削除済みを除外"""
        employee1 = EmployeeFactory.create(name='山田太郎')
        employee2 = EmployeeFactory.create(name='田中花子')

        employee1.delete()  # 論理削除

        # デフォルトマネージャーでは削除済みを除外
        employees = Employee.objects.all()
        assert employee2 in employees
        assert employee1 not in employees

    def test_with_deleted_includes_all(self):
        """with_deleted()は削除済みも含む"""
        employee1 = EmployeeFactory.create(name='山田太郎')
        employee2 = EmployeeFactory.create(name='田中花子')

        employee1.delete()  # 論理削除

        # with_deleted()で削除済みも含む
        employees = Employee.objects.with_deleted()
        assert employee1 in employees
        assert employee2 in employees

    def test_only_deleted(self):
        """only_deleted()は削除済みのみ"""
        employee1 = EmployeeFactory.create(name='山田太郎')
        employee2 = EmployeeFactory.create(name='田中花子')

        employee1.delete()  # 論理削除

        # only_deleted()で削除済みのみ
        deleted_employees = Employee.objects.only_deleted()
        assert employee1 in deleted_employees
        assert employee2 not in deleted_employees

    def test_filter_by_department(self):
        """組織で社員をフィルタリング"""
        org1 = DepartmentFactory.create(name='営業部')
        org2 = DepartmentFactory.create(name='開発部')

        employee1 = EmployeeFactory.create(department=org1)
        employee2 = EmployeeFactory.create(department=org1)
        employee3 = EmployeeFactory.create(department=org2)

        # 営業部の社員を取得
        sales_employees = Employee.objects.filter(department=org1)

        assert employee1 in sales_employees
        assert employee2 in sales_employees
        assert employee3 not in sales_employees


@pytest.mark.django_db
class TestEmployeeDepartmentDeleteScenarios:
    """社員と組織の削除シナリオのテスト"""

    def test_scenario_department_deleted_employees_become_unaffiliated(self):
        """シナリオ: 組織削除時に社員が未所属になる"""
        # 準備: 組織と社員を作成
        org = DepartmentFactory.create(name='営業部')
        employees = EmployeeFactory.create_batch(5, department=org)

        # 実行: 組織を論理削除
        org.delete()

        # 検証: 全社員が未所属になる
        for employee in employees:
            employee.refresh_from_db()
            assert employee.department is None

        # 検証: 社員は削除されていない
        assert Employee.objects.count() == 5

    def test_scenario_hierarchy_deleted_only_direct_employees_affected(self):
        """シナリオ: 階層構造で親組織削除時、直接所属する社員のみ影響を受ける"""
        # 準備: 組織階層を作成
        parent = DepartmentFactory.create(name='営業部')
        child = DepartmentFactory.create(name='営業一課', parent=parent)

        # 各組織に社員を追加
        parent_employees = EmployeeFactory.create_batch(2, department=parent)
        child_employees = EmployeeFactory.create_batch(2, department=child)

        # 実行: 親組織を論理削除
        parent.delete()

        # 検証: 親組織の社員は未所属になる
        for employee in parent_employees:
            employee.refresh_from_db()
            assert employee.department is None

        # 検証: 子組織の社員はそのまま
        for employee in child_employees:
            employee.refresh_from_db()
            assert employee.department == child

        # 検証: 子組織はルート組織化される
        child.refresh_from_db()
        assert child.parent is None

    def test_scenario_delete_department_then_restore(self):
        """シナリオ: 組織削除後に復元しても社員は未所属のまま"""
        # 準備
        org = DepartmentFactory.create(name='営業部')
        employees = EmployeeFactory.create_batch(3, department=org)

        # 実行: 組織を論理削除
        org.delete()

        # 検証: 社員が未所属になる
        for employee in employees:
            employee.refresh_from_db()
            assert employee.department is None

        # 実行: 組織を復元
        org.restore()

        # 検証: 社員は未所属のまま（自動的には戻らない）
        for employee in employees:
            employee.refresh_from_db()
            assert employee.department is None

        # 手動で再設定が必要
        for employee in employees:
            employee.department = org
            employee.save()

        for employee in employees:
            employee.refresh_from_db()
            assert employee.department == org
