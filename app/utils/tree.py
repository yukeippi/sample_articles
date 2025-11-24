from typing import Any


def build_tree(items: list[dict[str, Any]], parent_key: str = 'parent') -> list[dict[str, Any]]:
    """
    フラットな組織リストから階層ツリーを構築する

    Args:
        items: 組織データのリスト（各要素は辞書）
        parent_key: 親IDを示すキー名

    Returns:
        ツリー構造のリスト
    """
    # IDをキーとした辞書を作成
    nodes = {}
    for item in items:
        item_copy = item.copy()
        item_copy['children'] = []
        nodes[item['id']] = item_copy

    # ツリーを構築
    roots = []
    for item in items:
        node = nodes[item['id']]
        parent_id = item.get(parent_key)

        if parent_id is None:
            # ルートノード
            roots.append(node)
        elif parent_id in nodes:
            # 親ノードが存在する場合、子として追加
            nodes[parent_id]['children'].append(node)
        else:
            # 親ノードが存在しない場合（エラーケース）、ルートとして扱う
            roots.append(node)

    return roots


def _render_tree_node(node: dict[str, Any], level: int = 0) -> str:
    """ツリーノードをHTML文字列としてレンダリング"""
    indent = '  ' * level
    name = node.get('name', 'Unknown')
    node_id = node.get('id', '')

    html = f'{indent}<li>\n'
    html += f'{indent}  <span class="tree-node" data-id="{node_id}">{name}</span>\n'

    children = node.get('children', [])
    if children:
        html += f'{indent}  <ul class="tree-children">\n'
        for child in children:
            html += _render_tree_node(child, level + 2)
        html += f'{indent}  </ul>\n'

    html += f'{indent}</li>\n'
    return html


def get_tree_html(tree: list[dict[str, Any]]) -> str:
    """
    ツリー構造をHTMLとして出力

    Args:
        tree: build_tree関数で構築されたツリー構造

    Returns:
        HTML文字列
    """
    if not tree:
        return '<p class="text-muted">組織データがありません</p>'

    html = '<ul class="tree-root">\n'
    for node in tree:
        html += _render_tree_node(node, level=1)
    html += '</ul>\n'

    return html
