from django import forms

from app.models import Article, Organization, OrganizationReservation


class ArticleForm(forms.ModelForm):
    """記事の作成・編集フォーム"""

    class Meta:
        model = Article
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'タイトルを入力'}
            ),
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


class OrganizationForm(forms.ModelForm):
    """組織の作成・編集フォーム"""

    class Meta:
        model = Organization
        fields = ['name', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '組織名を入力'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': '組織名',
            'parent': '親組織',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].required = False
        self.fields['parent'].queryset = Organization.objects.all()


class OrganizationReservationForm(forms.ModelForm):
    """組織予約更新フォーム"""

    class Meta:
        model = OrganizationReservation
        fields = ['organization', 'action', 'name', 'parent', 'scheduled_date']
        widgets = {
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'action': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '組織名を入力'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
        }
        labels = {
            'organization': '対象組織',
            'action': '操作種別',
            'name': '組織名',
            'parent': '親組織',
            'scheduled_date': '適用予定日',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organization'].required = False
        self.fields['name'].required = False
        self.fields['parent'].required = False
        self.fields['organization'].queryset = Organization.objects.all()
        self.fields['parent'].queryset = Organization.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        organization = cleaned_data.get('organization')
        name = cleaned_data.get('name')

        if action == OrganizationReservation.ACTION_CREATE:
            if not name:
                raise forms.ValidationError('新規作成の場合、組織名は必須です。')
            if organization:
                raise forms.ValidationError('新規作成の場合、対象組織は指定できません。')
        elif action in [
            OrganizationReservation.ACTION_UPDATE,
            OrganizationReservation.ACTION_DELETE,
        ]:
            if not organization:
                raise forms.ValidationError('更新/削除の場合、対象組織は必須です。')

        return cleaned_data
