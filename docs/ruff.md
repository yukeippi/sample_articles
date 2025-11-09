# Ruff - Python Linter & Formatter

このプロジェクトでは、静的コード解析とフォーマットに**Ruff**を使用しています。

## Ruffとは

Ruffは、Rust製の超高速なPython linter/formatterです。以下のツールを置き換えることができます：

- **Flake8** (+ plugins)
- **isort**
- **pyupgrade**
- **Black** (formatter)

## インストール

Ruffは開発依存関係としてインストール済みです：

```bash
uv add --dev ruff
```

## 使い方

### コードのチェック

```bash
# デフォルトで app/ と config/ をチェック
ruff check

# 特定のディレクトリをチェック
ruff check app/

# 統計情報を表示
ruff check --statistics
```

### 自動修正

```bash
# 自動修正可能なエラーを修正
ruff check --fix

# 安全でない修正も含める
ruff check --fix --unsafe-fixes
```

### コードのフォーマット

```bash
# フォーマットをチェック
ruff format --check

# フォーマットを適用
ruff format
```

### 統合コマンド

```bash
# チェック + フォーマット
ruff check --fix && ruff format
```

## 設定

設定は [`pyproject.toml`](../pyproject.toml) の `[tool.ruff]` セクションで管理しています。

### 主な設定内容

#### 有効化しているルール

- **E, W**: pycodestyle (エラーと警告)
- **F**: Pyflakes (未使用のインポートなど)
- **I**: isort (インポートの並び順)
- **N**: pep8-naming (命名規則)
- **UP**: pyupgrade (Python構文の最新化)
- **B**: flake8-bugbear (バグになりやすいパターン)
- **C4**: flake8-comprehensions (内包表記の最適化)
- **DJ**: flake8-django (Django固有のチェック)
- **DTZ**: flake8-datetimez (タイムゾーン対応)
- **RUF**: Ruff固有のルール
- **SIM**: flake8-simplify (コードの簡素化)
- **PTH**: flake8-use-pathlib (pathlibの使用)

#### 無視しているルール

- **E501**: 行の長さ制限 (フォーマッターが処理)
- **DJ001**: 文字列フィールドのnull=True (プロジェクトの方針)
- **RUF001**: 曖昧なUnicode文字 (日本語対応のため)
- **RUF002**: docstringの曖昧なUnicode文字 (日本語対応のため)
- **RUF003**: コメントの曖昧なUnicode文字 (日本語対応のため)
- **RUF012**: Mutableなクラスデフォルト (Djangoのmigrationsのため)

#### config ディレクトリで追加で無視しているルール

- **F403**: Star imports (設定ファイルの一般的なパターン)
- **F405**: Star importsからの未定義
- **PTH118**: os.path.join() の使用を許可
- **PTH110**: os.path.exists() の使用を許可

#### その他の設定

- **Python バージョン**: 3.14
- **行の長さ**: 100文字
- **クォート**: シングルクォート (`'`)
- **デフォルトチェック対象**: `app/` と `config/`
- **除外ディレクトリ**: `.git`, `.venv`, `migrations`, `__pycache__`など

## CI/CD統合

### GitHub Actions

```yaml
- name: Lint with Ruff
  run: |
    ruff check .
    ruff format --check .
```

### Pre-commit Hook

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

## エディタ統合

### VS Code

拡張機能をインストール：

```
charliermarsh.ruff
```

`settings.json`:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  }
}
```

### PyCharm

Settings → Tools → External Tools でRuffを設定

## よくあるエラーと対処法

### F401: Unused import

```python
# Bad
import os
import sys

# Good
import sys  # osは使われていないので削除
```

### I001: Unsorted imports

```python
# Bad
from django.db import models
from app.models import Article
import os

# Good (自動修正可能)
import os

from django.db import models

from app.models import Article
```

### B904: raise without from

```python
# Bad
try:
    something()
except Exception as e:
    raise CustomError("Error")

# Good
try:
    something()
except Exception as e:
    raise CustomError("Error") from e
```

## 参考リンク

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Ruff Rules](https://docs.astral.sh/ruff/rules/)
- [Ruff Configuration](https://docs.astral.sh/ruff/configuration/)
