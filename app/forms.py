from django import forms

from app.models import Article


class ArticleForm(forms.ModelForm):
    """記事の作成・編集フォーム"""

    class Meta:
        model = Article
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'タイトルを入力'}),
            'content': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': '本文を入力',
                    'rows': 10,
                }
            ),
        }
        labels = {
            'title': 'タイトル',
            'content': '本文',
        }
