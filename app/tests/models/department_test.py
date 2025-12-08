"""
組織モデルのテスト
"""

import pytest
from django.db.models import ProtectedError

from app.models import Employee, Department
from app.tests.factories import (
    EmployeeFactory,
    DepartmentFactory,
    create_department_hierarchy,
    create_department_with_employees,
)


@pytest.mark.django_db
class TestDepartmentModel:
    """組織モデルのテスト"""

    def test_create_root_department(self):
        """ルート組織の作成"""
        org = DepartmentFactory.create(name='本社', parent=None)

        assert org.name == '本社'
        assert org.parent is None
        assert org.get_level() == 0

    def test_create_child_department(self):
        """子組織の作成"""
        parent = DepartmentFactory.create(name='本社')
        child = DepartmentFactory.create(name='営業部', parent=parent)

        assert child.parent == parent
        assert child.get_level() == 1
        assert child in parent.children.all()

    def test_get_ancestors(self):
        """先祖組織の取得"""
        hierarchy = create_department_hierarchy()
        grandchild = hierarchy['grandchildren'][0]

        ancestors = grandchild.get_ancestors()

        assert len(ancestors) == 2
        assert hierarchy['children'][0] in ancestors
        assert hierarchy['parent'] in ancestors

    def test_get_descendants(self):
        """子孫組織の取得"""
        hierarchy = create_department_hierarchy()
        parent = hierarchy['parent']

        descendants = parent.get_descendants()

        assert len(descendants) == 4  # 子2 + 孫2
        for child in hierarchy['children']:
            assert child in descendants
        for grandchild in hierarchy['grandchildren']:
            assert grandchild in descendants

    def test_get_level(self):
        """階層レベルの取得"""
        hierarchy = create_department_hierarchy()

        assert hierarchy['parent'].get_level() == 0
        assert hierarchy['children'][0].get_level() == 1
        assert hierarchy['grandchildren'][0].get_level() == 2

    def test_str_representation(self):
        """文字列表現"""
        org = DepartmentFactory.create(name='営業部')
        assert str(org) == '営業部'


@pytest.mark.django_db
class TestDepartmentSoftDelete:
    """組織の論理削除のテスト"""

    def test_soft_delete(self):
        """論理削除"""
        org = DepartmentFactory.create(name='営業部')
        org_id = org.id

        # 論理削除を実行
        org.delete()

        # デフォルトのマネージャーでは取得できない
        assert not Department.objects.filter(id=org_id).exists()

        # with_deleted() で取得可能
        deleted_org = Department.objects.with_deleted().get(id=org_id)
        assert deleted_org.is_deleted
        assert deleted_org.deleted_at is not None

    def test_soft_delete_sets_children_parent_to_null(self):
        """論理削除時に子組織の親がNULLになる"""
        parent = DepartmentFactory.create(name='営業部')
        child1 = DepartmentFactory.create(name='営業一課', parent=parent)
        child2 = DepartmentFactory.create(name='営業二課', parent=parent)

        # 親組織を論理削除
        parent.delete()

        # 子組織の親がNULLになる（ルート組織化）
        child1.refresh_from_db()
        child2.refresh_from_db()

        assert child1.parent is None
        assert child2.parent is None
        assert child1.get_level() == 0
        assert child2.get_level() == 0

    def test_soft_delete_sets_employees_department_to_null(self):
        """論理削除時に所属社員の組織がNULLになる"""
        org, employees = create_department_with_employees(num_employees=3)

        # 組織を論理削除
        org.delete()

        # 所属社員の組織がNULLになる（未所属化）
        for employee in employees:
            employee.refresh_from_db()
            assert employee.department is None

    def test_soft_delete_with_hierarchy_and_employees(self):
        """階層構造と社員を持つ組織の論理削除"""
        parent = DepartmentFactory.create(name='営業部')
        child1 = DepartmentFactory.create(name='営業一課', parent=parent)
        child2 = DepartmentFactory.create(name='営業二課', parent=parent)

        # 親組織に社員を追加
        parent_employees = EmployeeFactory.create_batch(2, department=parent)

        # 子組織に社員を追加
        child1_employees = EmployeeFactory.create_batch(2, department=child1)
        child2_employees = EmployeeFactory.create_batch(2, department=child2)

        # 親組織を論理削除
        parent.delete()

        # 親組織は論理削除される
        parent.refresh_from_db()
        assert parent.is_deleted

        # 親組織の社員は未所属になる
        for employee in parent_employees:
            employee.refresh_from_db()
            assert employee.department is None

        # 子組織はルート組織化される
        child1.refresh_from_db()
        child2.refresh_from_db()
        assert child1.parent is None
        assert child2.parent is None

        # 子組織の社員はそのまま（親組織の削除では影響を受けない）
        for employee in child1_employees:
            employee.refresh_from_db()
            assert employee.department == child1

        for employee in child2_employees:
            employee.refresh_from_db()
            assert employee.department == child2

    def test_restore(self):
        """論理削除の復元"""
        org = DepartmentFactory.create(name='営業部')

        # 論理削除
        org.delete()
        assert org.is_deleted

        # 復元
        org.restore()
        assert not org.is_deleted
        assert org.deleted_at is None

        # デフォルトのマネージャーで取得可能
        assert Department.objects.filter(id=org.id).exists()

    def test_hard_delete(self):
        """物理削除"""
        org = DepartmentFactory.create(name='営業部')
        org_id = org.id

        # 物理削除
        org.hard_delete()

        # どのマネージャーでも取得不可
        assert not Department.objects.with_deleted().filter(id=org_id).exists()
        assert not Department.all_objects.filter(id=org_id).exists()

    def test_hard_delete_cascades_to_children(self):
        """物理削除時にCASCADE制約で子組織も削除される"""
        parent = DepartmentFactory.create(name='営業部')
        child = DepartmentFactory.create(name='営業一課', parent=parent)
        child_id = child.id

        # 親組織を物理削除
        parent.hard_delete()

        # 子組織も物理削除される
        assert not Department.objects.with_deleted().filter(id=child_id).exists()

    def test_hard_delete_protected_by_employees(self):
        """社員が存在する場合、物理削除はPROTECT制約でエラーになる"""
        org = DepartmentFactory.create(name='営業部')
        EmployeeFactory.create(department=org)

        # 物理削除しようとするとProtectedError
        with pytest.raises(ProtectedError):
            org.hard_delete()


@pytest.mark.django_db
class TestDepartmentQueries:
    """組織のクエリのテスト"""

    def test_default_manager_excludes_deleted(self):
        """デフォルトマネージャーは削除済みを除外"""
        org1 = DepartmentFactory.create(name='営業部')
        org2 = DepartmentFactory.create(name='開発部')

        org1.delete()  # 論理削除

        # デフォルトマネージャーでは削除済みを除外
        orgs = Department.objects.all()
        assert org2 in orgs
        assert org1 not in orgs

    def test_with_deleted_includes_all(self):
        """with_deleted()は削除済みも含む"""
        org1 = DepartmentFactory.create(name='営業部')
        org2 = DepartmentFactory.create(name='開発部')

        org1.delete()  # 論理削除

        # with_deleted()で削除済みも含む
        orgs = Department.objects.with_deleted()
        assert org1 in orgs
        assert org2 in orgs

    def test_only_deleted(self):
        """only_deleted()は削除済みのみ"""
        org1 = DepartmentFactory.create(name='営業部')
        org2 = DepartmentFactory.create(name='開発部')

        org1.delete()  # 論理削除

        # only_deleted()で削除済みのみ
        deleted_orgs = Department.objects.only_deleted()
        assert org1 in deleted_orgs
        assert org2 not in deleted_orgs


@pytest.mark.django_db
class TestDepartmentMerge:
    """組織統合のテスト"""

    def test_merge_basic(self):
        """基本的な組織統合"""
        org_a = DepartmentFactory.create(name='組織A')
        org_b = DepartmentFactory.create(name='組織B')

        # 組織Bを組織Aに統合
        org_b.merge_into(org_a)

        # 組織Bは論理削除される
        assert not Department.objects.filter(id=org_b.id).exists()
        org_b_deleted = Department.objects.with_deleted().get(id=org_b.id)
        assert org_b_deleted.is_deleted

        # 組織Aは残る
        assert Department.objects.filter(id=org_a.id).exists()

    def test_merge_transfers_employees(self):
        """組織統合で社員が移動する"""
        org_a = DepartmentFactory.create(name='組織A')
        org_b = DepartmentFactory.create(name='組織B')

        # 組織Bに社員を追加
        employees_b = EmployeeFactory.create_batch(3, department=org_b)

        # 組織Bを組織Aに統合
        org_b.merge_into(org_a)

        # 組織Bの社員が組織Aに移動
        for employee in employees_b:
            employee.refresh_from_db()
            assert employee.department == org_a

    def test_merge_transfers_children(self):
        """組織統合で子組織が移動する"""
        org_a = DepartmentFactory.create(name='組織A')
        org_b = DepartmentFactory.create(name='組織B')

        # 組織Bに子組織を追加
        child1 = DepartmentFactory.create(name='組織B-子1', parent=org_b)
        child2 = DepartmentFactory.create(name='組織B-子2', parent=org_b)

        # 組織Bを組織Aに統合
        org_b.merge_into(org_a)

        # 組織Bの子組織が組織Aの子組織になる
        child1.refresh_from_db()
        child2.refresh_from_db()
        assert child1.parent == org_a
        assert child2.parent == org_a

    def test_merge_with_employees_and_children(self):
        """社員と子組織の両方がある組織の統合"""
        org_a = DepartmentFactory.create(name='組織A')
        org_b = DepartmentFactory.create(name='組織B')

        # 組織Bに社員と子組織を追加
        employees_b = EmployeeFactory.create_batch(2, department=org_b)
        child1 = DepartmentFactory.create(name='組織B-子1', parent=org_b)
        child2 = DepartmentFactory.create(name='組織B-子2', parent=org_b)

        # 子組織にも社員を追加
        child1_employees = EmployeeFactory.create_batch(2, department=child1)

        # 組織Bを組織Aに統合
        org_b.merge_into(org_a)

        # 組織Bの社員が組織Aに移動
        for employee in employees_b:
            employee.refresh_from_db()
            assert employee.department == org_a

        # 組織Bの子組織が組織Aの子組織になる
        child1.refresh_from_db()
        child2.refresh_from_db()
        assert child1.parent == org_a
        assert child2.parent == org_a

        # 子組織の社員はそのまま
        for employee in child1_employees:
            employee.refresh_from_db()
            assert employee.department == child1

    def test_merge_to_self_raises_error(self):
        """自分自身への統合はエラー"""
        org = DepartmentFactory.create(name='組織A')

        with pytest.raises(ValueError, match='自分自身に統合することはできません'):
            org.merge_into(org)

    def test_merge_to_deleted_department_raises_error(self):
        """削除済み組織への統合はエラー"""
        org_a = DepartmentFactory.create(name='組織A')
        org_b = DepartmentFactory.create(name='組織B')

        # 組織Aを削除
        org_a.delete()

        with pytest.raises(ValueError, match='削除済みの組織には統合できません'):
            org_b.merge_into(org_a)

    def test_merge_to_descendant_raises_error(self):
        """子孫組織への統合はエラー"""
        parent = DepartmentFactory.create(name='親組織')
        child = DepartmentFactory.create(name='子組織', parent=parent)
        grandchild = DepartmentFactory.create(name='孫組織', parent=child)

        # 親組織を子組織に統合しようとするとエラー
        with pytest.raises(ValueError, match='子孫組織には統合できません'):
            parent.merge_into(child)

        # 親組織を孫組織に統合しようとするとエラー
        with pytest.raises(ValueError, match='子孫組織には統合できません'):
            parent.merge_into(grandchild)

    def test_merge_invalid_target_type_raises_error(self):
        """無効な型の統合先を指定するとエラー"""
        org = DepartmentFactory.create(name='組織A')

        with pytest.raises(ValueError, match='統合先は組織オブジェクトである必要があります'):
            org.merge_into('invalid_type')

    def test_merge_preserves_target_department(self):
        """統合先組織は変更されない"""
        org_a = DepartmentFactory.create(name='組織A')
        org_b = DepartmentFactory.create(name='組織B')

        # 組織Aに既存の社員を追加
        employees_a = EmployeeFactory.create_batch(2, department=org_a)

        # 組織Bに社員を追加
        employees_b = EmployeeFactory.create_batch(3, department=org_b)

        # 組織Bを組織Aに統合
        org_b.merge_into(org_a)

        # 組織Aの既存社員はそのまま
        for employee in employees_a:
            employee.refresh_from_db()
            assert employee.department == org_a

        # 組織Aの社員数が増えている
        org_a.refresh_from_db()
        assert org_a.employees.count() == 5  # 元の2人 + 統合された3人
