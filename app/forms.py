from django import forms

from app.models import Article, Employee, Organization, Reservation


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


class OrganizationReservationForm(forms.Form):
    """組織予約更新フォーム"""

    ACTION_CHOICES = [
        ('create', '新規作成'),
        ('update', '更新'),
        ('delete', '削除'),
    ]

    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        label='対象組織',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        label='操作種別',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    name = forms.CharField(
        max_length=200,
        required=False,
        label='組織名',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '組織名を入力'}),
    )
    parent = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        label='親組織（既存）',
        help_text='既存の組織を親として選択',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    parent_reservation = forms.ModelChoiceField(
        queryset=Reservation.objects.none(),  # 初期化時に設定
        required=False,
        label='親組織（未来の予約）',
        help_text='未適用の新規作成予約を親として指定する場合に選択',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    scheduled_date = forms.DateField(
        label='適用予定日',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 予約中の組織新規作成予約を parent_reservation の選択肢に設定
        from app.utils.organization_reservation import OrganizationReservationHelper
        pending_reservations = OrganizationReservationHelper.get_pending_reservations()
        create_reservations = pending_reservations.filter(action=Reservation.ACTION_CREATE)

        # 選択肢をわかりやすく表示
        self.fields['parent_reservation'].queryset = create_reservations
        self.fields['parent_reservation'].label_from_instance = lambda obj: (
            f"{obj.data.get('name', '不明')} (予定日: {obj.scheduled_date})"
        )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        organization = cleaned_data.get('organization')
        name = cleaned_data.get('name')
        parent = cleaned_data.get('parent')
        parent_reservation = cleaned_data.get('parent_reservation')

        if action == 'create':
            if not name:
                raise forms.ValidationError('新規作成の場合、組織名は必須です。')
            if organization:
                raise forms.ValidationError('新規作成の場合、対象組織は指定できません。')
        elif action in ['update', 'delete']:
            if not organization:
                raise forms.ValidationError('更新/削除の場合、対象組織は必須です。')

        # 親組織と親予約の両方が指定されている場合はエラー
        if parent and parent_reservation:
            raise forms.ValidationError('親組織（既存）と親組織（未来の予約）は同時に指定できません。どちらか一方を選択してください。')

        return cleaned_data


class EmployeeForm(forms.ModelForm):
    """社員の作成・編集フォーム"""

    class Meta:
        model = Employee
        fields = ['name', 'email', 'organization']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '氏名を入力'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'メールアドレスを入力'}),
            'organization': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': '氏名',
            'email': 'メールアドレス',
            'organization': '所属組織',
        }
