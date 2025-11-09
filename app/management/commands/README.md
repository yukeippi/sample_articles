# カスタム管理コマンド

このディレクトリには、Djangoのカスタム管理コマンドが含まれています。

## reset_database コマンド

PostgreSQLデータベースを完全にリセット（削除、作成、マイグレーション）するコマンドです。
Railsの`rails db:drop; rails db:create; rails db:migrate`に相当します。

内部的には`django-extensions`の`reset_db`コマンドを使用し、利用できない場合は`flush`にフォールバックします。

### 基本的な使い方

```bash
# 確認付きでリセット
python manage.py reset_database

# 確認なしでリセット
python manage.py reset_database --noinput

# リセット後に初期データも投入
python manage.py reset_database --seed

# 確認なし + 初期データ投入
python manage.py reset_database --noinput --seed
```

### オプション

#### --noinput
確認なしで実行します。

#### --seed
リセット後に`seed_data`コマンドを実行して初期データを投入します。

### 使用例

開発環境をクリーンな状態にリセットして初期データを投入：
```bash
python manage.py reset_database --noinput --seed
```

## seed_data コマンド

初期データを投入するコマンドです。開発環境やテスト環境でサンプルデータを用意する際に使用します。

### 投入されるデータ

- **ユーザー**: 太郎、花子、次郎（各3名）
- **記事**: 3件（各ユーザーが1件ずつ投稿）
- **コメント**: 4件（記事へのコメント）

### 基本的な使い方

```bash
python manage.py seed_data
```

### オプション

#### --clear
既存のデータを削除してから初期データを投入します。
（注意: スーパーユーザー以外のユーザーも削除されます）

```bash
python manage.py seed_data --clear
```

### ヘルプの表示

```bash
python manage.py seed_data --help
```

## データベースをリセットする他の方法

### 1. flush コマンド

全てのデータを削除しますが、テーブル構造は残ります：

```bash
python manage.py flush
```

### 2. reset_db コマンド（django-extensions）

django-extensionsを使用している場合、直接実行することもできます：

```bash
python manage.py reset_db --close-sessions
python manage.py migrate
```

## その他のデータ投入方法

### 1. Djangoシェルで直接実行

一度きりのスクリプトを実行したい場合：

```bash
python manage.py shell < script.py
```

または`django-extensions`の`shell_plus`を使って：

```bash
python manage.py shell_plus --command="実行するコード"
```

### 2. Fixturesを使う方法

JSON/YAML形式でデータを定義して読み込む方法：

```bash
# データをエクスポート
python manage.py dumpdata app.Article app.Comment > fixtures/initial_data.json

# データをインポート
python manage.py loaddata fixtures/initial_data.json
```

## カスタムコマンドの追加方法

1. このディレクトリに新しい`.py`ファイルを作成
2. `BaseCommand`を継承した`Command`クラスを定義
3. `handle()`メソッドを実装

例：

```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'コマンドの説明'

    def add_arguments(self, parser):
        # オプション引数を追加
        parser.add_argument('--option', type=str, help='オプションの説明')

    def handle(self, *args, **options):
        # コマンドの処理を実装
        self.stdout.write(self.style.SUCCESS('成功しました'))
```

詳細は[Django公式ドキュメント](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)を参照してください。
