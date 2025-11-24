"""
組織モデルのテスト
"""

import pytest
from django.db.models import ProtectedError

from app.models import Employee, Organization
from app.tests.factories import (
    EmployeeFactory,
    OrganizationFactory,
    create_organization_hierarchy,
    create_organization_with_employees,
)


@pytest.mark.django_db
class TestOrganizationModel:
    """組織モデルのテスト"""

    def test_create_root_organization(self):
        """ルート組織の作成"""
        org = OrganizationFactory.create(name='本社', parent=None)

        assert org.name == '本社'
        assert org.parent is None
        assert org.get_level() == 0

    def test_create_child_organization(self):
        """子組織の作成"""
        parent = OrganizationFactory.create(name='本社')
        child = OrganizationFactory.create(name='営業部', parent=parent)

        assert child.parent == parent
        assert child.get_level() == 1
        assert child in parent.children.all()

    def test_get_ancestors(self):
        """先祖組織の取得"""
        hierarchy = create_organization_hierarchy()
        grandchild = hierarchy['grandchildren'][0]

        ancestors = grandchild.get_ancestors()

        assert len(ancestors) == 2
        assert hierarchy['children'][0] in ancestors
        assert hierarchy['parent'] in ancestors

    def test_get_descendants(self):
        """子孫組織の取得"""
        hierarchy = create_organization_hierarchy()
        parent = hierarchy['parent']

        descendants = parent.get_descendants()

        assert len(descendants) == 4  # 子2 + 孫2
        for child in hierarchy['children']:
            assert child in descendants
        for grandchild in hierarchy['grandchildren']:
            assert grandchild in descendants

    def test_get_level(self):
        """階層レベルの取得"""
        hierarchy = create_organization_hierarchy()

        assert hierarchy['parent'].get_level() == 0
        assert hierarchy['children'][0].get_level() == 1
        assert hierarchy['grandchildren'][0].get_level() == 2

    def test_str_representation(self):
        """文字列表現"""
        org = OrganizationFactory.create(name='営業部')
        assert str(org) == '営業部'


@pytest.mark.django_db
class TestOrganizationSoftDelete:
    """組織の論理削除のテスト"""

    def test_soft_delete(self):
        """論理削除"""
        org = OrganizationFactory.create(name='営業部')
        org_id = org.id

        # 論理削除を実行
        org.delete()

        # デフォルトのマネージャーでは取得できない
        assert not Organization.objects.filter(id=org_id).exists()

        # with_deleted() で取得可能
        deleted_org = Organization.objects.with_deleted().get(id=org_id)
        assert deleted_org.is_deleted
        assert deleted_org.deleted_at is not None

    def test_soft_delete_sets_children_parent_to_null(self):
        """論理削除時に子組織の親がNULLになる"""
        parent = OrganizationFactory.create(name='営業部')
        child1 = OrganizationFactory.create(name='営業一課', parent=parent)
        child2 = OrganizationFactory.create(name='営業二課', parent=parent)

        # 親組織を論理削除
        parent.delete()

        # 子組織の親がNULLになる（ルート組織化）
        child1.refresh_from_db()
        child2.refresh_from_db()

        assert child1.parent is None
        assert child2.parent is None
        assert child1.get_level() == 0
        assert child2.get_level() == 0

    def test_soft_delete_sets_employees_organization_to_null(self):
        """論理削除時に所属社員の組織がNULLになる"""
        org, employees = create_organization_with_employees(num_employees=3)

        # 組織を論理削除
        org.delete()

        # 所属社員の組織がNULLになる（未所属化）
        for employee in employees:
            employee.refresh_from_db()
            assert employee.organization is None

    def test_soft_delete_with_hierarchy_and_employees(self):
        """階層構造と社員を持つ組織の論理削除"""
        parent = OrganizationFactory.create(name='営業部')
        child1 = OrganizationFactory.create(name='営業一課', parent=parent)
        child2 = OrganizationFactory.create(name='営業二課', parent=parent)

        # 親組織に社員を追加
        parent_employees = EmployeeFactory.create_batch(2, organization=parent)

        # 子組織に社員を追加
        child1_employees = EmployeeFactory.create_batch(2, organization=child1)
        child2_employees = EmployeeFactory.create_batch(2, organization=child2)

        # 親組織を論理削除
        parent.delete()

        # 親組織は論理削除される
        parent.refresh_from_db()
        assert parent.is_deleted

        # 親組織の社員は未所属になる
        for employee in parent_employees:
            employee.refresh_from_db()
            assert employee.organization is None

        # 子組織はルート組織化される
        child1.refresh_from_db()
        child2.refresh_from_db()
        assert child1.parent is None
        assert child2.parent is None

        # 子組織の社員はそのまま（親組織の削除では影響を受けない）
        for employee in child1_employees:
            employee.refresh_from_db()
            assert employee.organization == child1

        for employee in child2_employees:
            employee.refresh_from_db()
            assert employee.organization == child2

    def test_restore(self):
        """論理削除の復元"""
        org = OrganizationFactory.create(name='営業部')

        # 論理削除
        org.delete()
        assert org.is_deleted

        # 復元
        org.restore()
        assert not org.is_deleted
        assert org.deleted_at is None

        # デフォルトのマネージャーで取得可能
        assert Organization.objects.filter(id=org.id).exists()

    def test_hard_delete(self):
        """物理削除"""
        org = OrganizationFactory.create(name='営業部')
        org_id = org.id

        # 物理削除
        org.hard_delete()

        # どのマネージャーでも取得不可
        assert not Organization.objects.with_deleted().filter(id=org_id).exists()
        assert not Organization.all_objects.filter(id=org_id).exists()

    def test_hard_delete_cascades_to_children(self):
        """物理削除時にCASCADE制約で子組織も削除される"""
        parent = OrganizationFactory.create(name='営業部')
        child = OrganizationFactory.create(name='営業一課', parent=parent)
        child_id = child.id

        # 親組織を物理削除
        parent.hard_delete()

        # 子組織も物理削除される
        assert not Organization.objects.with_deleted().filter(id=child_id).exists()

    def test_hard_delete_protected_by_employees(self):
        """社員が存在する場合、物理削除はPROTECT制約でエラーになる"""
        org = OrganizationFactory.create(name='営業部')
        EmployeeFactory.create(organization=org)

        # 物理削除しようとするとProtectedError
        with pytest.raises(ProtectedError):
            org.hard_delete()


@pytest.mark.django_db
class TestOrganizationQueries:
    """組織のクエリのテスト"""

    def test_default_manager_excludes_deleted(self):
        """デフォルトマネージャーは削除済みを除外"""
        org1 = OrganizationFactory.create(name='営業部')
        org2 = OrganizationFactory.create(name='開発部')

        org1.delete()  # 論理削除

        # デフォルトマネージャーでは削除済みを除外
        orgs = Organization.objects.all()
        assert org2 in orgs
        assert org1 not in orgs

    def test_with_deleted_includes_all(self):
        """with_deleted()は削除済みも含む"""
        org1 = OrganizationFactory.create(name='営業部')
        org2 = OrganizationFactory.create(name='開発部')

        org1.delete()  # 論理削除

        # with_deleted()で削除済みも含む
        orgs = Organization.objects.with_deleted()
        assert org1 in orgs
        assert org2 in orgs

    def test_only_deleted(self):
        """only_deleted()は削除済みのみ"""
        org1 = OrganizationFactory.create(name='営業部')
        org2 = OrganizationFactory.create(name='開発部')

        org1.delete()  # 論理削除

        # only_deleted()で削除済みのみ
        deleted_orgs = Organization.objects.only_deleted()
        assert org1 in deleted_orgs
        assert org2 not in deleted_orgs
