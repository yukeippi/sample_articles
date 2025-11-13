from django import template
from django.forms.widgets import (
    CheckboxInput,
    Select,
    Textarea,
    RadioSelect,
    SelectMultiple,
    FileInput,
)

register = template.Library()


def _merge_classes(existing: str | None, extra: str | None) -> str:
    ex = (existing or "").strip()
    add = (extra or "").strip()
    if not ex:
        return add
    if not add:
        return ex
    # 重複除去しながら結合
    merged = []
    for c in (ex + " " + add).split():
        if c not in merged:
            merged.append(c)
    return " ".join(merged)


@register.filter
def widget_class(field, base_class: str):
    """
    Bootstrap用のclassを付与して描画。
    - 既存classとマージ
    - エラー時に is-invalid を自動付与
    - フォームがバインド済みかつエラー無しなら is-valid も付与（任意：好みで外してOK）
    """
    existing = field.field.widget.attrs.get("class")
    cls = _merge_classes(existing, base_class)

    if getattr(field, "form", None) and field.form.is_bound:
        if field.errors:
            cls = _merge_classes(cls, "is-invalid")
        else:
            # 「成功時の緑枠」を付けたくない場合は、この行をコメントアウト
            cls = _merge_classes(cls, "is-valid")

    return field.as_widget(attrs={"class": cls})


@register.filter
def add_attr(field, arg: str):
    """
    任意属性を1つ追加して描画。
    使い方: {{ field|add_attr:"placeholder=タイトルを入力" }}
           {{ field|add_attr:"autocomplete=off" }}
    """
    try:
        key, val = arg.split("=", 1)
    except ValueError:
        return field  # フォーマット不正なら何もしない
    attrs = {key.strip(): val.strip()}
    return field.as_widget(attrs=attrs)


@register.filter
def add_class(field, extra_class: str):
    """
    既存classに追記して描画。
    使い方: {{ field|add_class:"form-control form-control-sm" }}
    """
    existing = field.field.widget.attrs.get("class")
    cls = _merge_classes(existing, extra_class)
    return field.as_widget(attrs={"class": cls})


@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, CheckboxInput)


@register.filter
def is_select(field):
    return isinstance(field.field.widget, Select)


@register.filter
def is_textarea(field):
    return isinstance(field.field.widget, Textarea)


@register.filter
def is_radio(field):
    return isinstance(field.field.widget, RadioSelect)


@register.filter
def is_select_multiple(field):
    return isinstance(field.field.widget, SelectMultiple)


@register.filter
def is_file(field):
    return isinstance(field.field.widget, FileInput)


@register.filter
def widget_a11y(field):
    """
    エラー時に aria-invalid を付与する。
    他のフィルタと組み合わせたい場合は、widget_classに統合でもOK。
    """
    attrs = {}
    if getattr(field, "form", None) and field.form.is_bound and field.errors:
        attrs["aria-invalid"] = "true"
    return field.as_widget(attrs=attrs)
