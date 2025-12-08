# モデルテスト

## 概要

このディレクトリには、組織（department）と社員（Employee）モデルのテストが含まれています。

## テストファイル

### department_test.py

組織モデルの全機能をテストします。

**テストクラス:**

1. **TestdepartmentModel** - 基本的なCRUD操作
   - ルート組織の作成
   - 子組織の作成
   - 先祖組織の取得
   - 子孫組織の取得
   - 階層レベルの取得
   - 文字列表現

2. **TestdepartmentSoftDelete** - 論理削除機能
   - 論理削除
   - 論理削除時に子組織の親がNULLになる
   - 論理削除時に所属社員の組織がNULLになる
   - 階層構造と社員を持つ組織の論理削除
   - 論理削除の復元
   - 物理削除
   - 物理削除時のCASCADE動作
   - 社員が存在する場合のPROTECT制約

3. **TestdepartmentQueries** - クエリ動作
   - デフォルトマネージャーは削除済みを除外
   - with_deleted()は削除済みも含む
   - only_deleted()は削除済みのみ

**テスト数:** 17個

### employee_test.py

社員モデルの全機能をテストします。

**テストクラス:**

1. **TestEmployeeModel** - 基本的なCRUD操作
   - 組織に所属する社員の作成
   - 未所属社員の作成
   - 文字列表現
   - メールアドレスの重複チェック
   - 論理削除された社員のメールアドレス再利用
   - 社員情報の更新

2. **TestEmployeeSoftDelete** - 論理削除機能
   - 論理削除
   - 論理削除の復元
   - 物理削除

3. **TestEmployeedepartmentRelationship** - 組織との関連
   - 組織の論理削除時に社員の組織がNULLになる
   - 社員の組織異動
   - 社員を未所属にする
   - 未所属社員のクエリ
   - 所属社員のクエリ
   - 社員が存在する組織は物理削除できない
   - 社員移動後に組織を物理削除
   - 社員未所属化後に組織を物理削除

4. **TestEmployeeQueries** - クエリ動作
   - デフォルトマネージャーは削除済みを除外
   - with_deleted()は削除済みも含む
   - only_deleted()は削除済みのみ
   - 組織でフィルタリング

5. **TestEmployeedepartmentDeleteScenarios** - 削除シナリオ
   - 組織削除時に社員が未所属になる
   - 階層構造で親組織削除時、直接所属する社員のみ影響
   - 組織削除後に復元しても社員は未所属のまま

**テスト数:** 24個

## テストの実行

### 全テスト実行

```bash
source .venv/bin/activate
python -m pytest app/tests/models/ -v
```

### 組織テストのみ

```bash
source .venv/bin/activate
python -m pytest app/tests/models/department_test.py -v
```

### 社員テストのみ

```bash
source .venv/bin/activate
python -m pytest app/tests/models/employee_test.py -v
```

### 特定のテストクラス実行

```bash
source .venv/bin/activate
python -m pytest app/tests/models/department_test.py::TestdepartmentSoftDelete -v
```

### 特定のテスト実行

```bash
source .venv/bin/activate
python -m pytest app/tests/models/department_test.py::TestdepartmentSoftDelete::test_soft_delete_sets_children_parent_to_null -v
```

## カバーされている主要な機能

### 論理削除（Soft Delete）

- ✅ 論理削除の基本動作
- ✅ 論理削除時の子組織のルート組織化（parent → NULL）
- ✅ 論理削除時の所属社員の未所属化（department → NULL）
- ✅ 論理削除の復元
- ✅ 削除済みレコードのクエリ（with_deleted, only_deleted）

### 物理削除（Hard Delete）

- ✅ 物理削除の基本動作
- ✅ CASCADE制約による子組織の削除
- ✅ PROTECT制約による削除防止

### 組織階層

- ✅ 親子関係の作成
- ✅ 先祖組織の取得
- ✅ 子孫組織の取得
- ✅ 階層レベルの取得

### 社員と組織の関連

- ✅ 組織に所属する社員の作成
- ✅ 未所属社員の作成
- ✅ 社員の組織異動
- ✅ メールアドレスのユニーク制約（論理削除対応）
- ✅ 組織削除時の社員への影響

### 複雑なシナリオ

- ✅ 階層構造を持つ組織の削除
- ✅ 社員を持つ組織の削除
- ✅ 組織復元後の社員の状態

## テストデータ作成

テストでは以下のファクトリを使用してテストデータを作成します：

- `departmentFactory.create()` - 組織を作成
- `EmployeeFactory.create()` - 社員を作成
- `create_department_hierarchy()` - 組織階層を作成
- `create_department_with_employees()` - 社員付き組織を作成

詳細は [../factories.py](../factories.py) を参照してください。

## 注意事項

- テストはトランザクション内で実行され、各テスト後にロールバックされます
- `@pytest.mark.django_db` デコレータを使用してデータベースアクセスを有効化しています
- faker を使用してランダムなテストデータを生成しています
