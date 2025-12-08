from django import forms

from app.models import Article, Employee, Department, Reservation


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


class DepartmentForm(forms.ModelForm):
    """組織の作成・編集フォーム"""

    class Meta:
        model = Department
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
        self.fields['parent'].queryset = Department.objects.all()


class DepartmentReservationForm(forms.Form):
    """組織予約更新フォーム"""

    ACTION_CHOICES = [
        ('create', '新規作成'),
        ('update', '更新'),
        ('delete', '削除'),
        ('merge', '統合'),
    ]

    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
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
        queryset=Department.objects.all(),
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
    target_department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label='統合先組織',
        help_text='統合の場合のみ：統合元組織がこの組織に取り込まれます',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    scheduled_date = forms.DateField(
        label='適用予定日',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 予約中の組織新規作成予約を parent_reservation の選択肢に設定
        from app.utils.department_reservation import DepartmentReservationHelper
        pending_reservations = DepartmentReservationHelper.get_pending_reservations()
        create_reservations = pending_reservations.filter(action=Reservation.ACTION_CREATE)

        # 選択肢をわかりやすく表示
        self.fields['parent_reservation'].queryset = create_reservations
        self.fields['parent_reservation'].label_from_instance = lambda obj: (
            f"{obj.data.get('name', '不明')} (予定日: {obj.scheduled_date})"
        )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        department = cleaned_data.get('department')
        name = cleaned_data.get('name')
        parent = cleaned_data.get('parent')
        parent_reservation = cleaned_data.get('parent_reservation')
        target_department = cleaned_data.get('target_department')

        if action == 'create':
            if not name:
                raise forms.ValidationError('新規作成の場合、組織名は必須です。')
            if department:
                raise forms.ValidationError('新規作成の場合、対象組織は指定できません。')
        elif action in ['update', 'delete']:
            if not department:
                raise forms.ValidationError('更新/削除の場合、対象組織は必須です。')
        elif action == 'merge':
            if not department:
                raise forms.ValidationError('統合の場合、統合元組織は必須です。')
            if not target_department:
                raise forms.ValidationError('統合の場合、統合先組織は必須です。')
            if department == target_department:
                raise forms.ValidationError('統合元と統合先に同じ組織を指定することはできません。')
            # 統合先が統合元の子孫でないかチェック
            if target_department in department.get_descendants():
                raise forms.ValidationError('統合元の子孫組織を統合先に指定することはできません。')

        # 親組織と親予約の両方が指定されている場合はエラー
        if parent and parent_reservation:
            raise forms.ValidationError('親組織（既存）と親組織（未来の予約）は同時に指定できません。どちらか一方を選択してください。')

        return cleaned_data


class EmployeeForm(forms.ModelForm):
    """社員の作成・編集フォーム"""

    class Meta:
        model = Employee
        fields = ['name', 'email', 'department']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '氏名を入力'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'メールアドレスを入力'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': '氏名',
            'email': 'メールアドレス',
            'department': '所属組織',
        }


class DepartmentMergeForm(forms.Form):
    """組織統合フォーム"""

    source_department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        label='統合元組織',
        help_text='この組織が統合先組織に取り込まれます',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    target_department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        label='統合先組織',
        help_text='統合元組織の社員と子組織がこの組織に移動します',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['source_department'].queryset = Department.objects.all()
        self.fields['target_department'].queryset = Department.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('source_department')
        target = cleaned_data.get('target_department')

        if source and target:
            # 同じ組織を選択していないかチェック
            if source.pk == target.pk:
                raise forms.ValidationError('統合元と統合先に同じ組織を指定することはできません。')

            # 統合先が削除済みでないかチェック
            if target.deleted_at is not None:
                raise forms.ValidationError('削除済みの組織を統合先に指定することはできません。')

            # 統合先が統合元の子孫でないかチェック
            if target in source.get_descendants():
                raise forms.ValidationError('統合元の子孫組織を統合先に指定することはできません。')

        return cleaned_data


class EmployeeReservationForm(forms.Form):
    """社員予約更新フォーム"""

    ACTION_CHOICES = [
        ('create', '新規作成'),
        ('update', '更新'),
        ('delete', '削除'),
    ]

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        label='対象社員',
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
        label='氏名',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '氏名を入力'}),
    )
    email = forms.EmailField(
        required=False,
        label='メールアドレス',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'メールアドレスを入力'}),
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label='所属組織',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    scheduled_date = forms.DateField(
        label='適用予定日',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        employee = cleaned_data.get('employee')
        name = cleaned_data.get('name')
        email = cleaned_data.get('email')

        if action == 'create':
            if not name:
                raise forms.ValidationError('新規作成の場合、氏名は必須です。')
            if not email:
                raise forms.ValidationError('新規作成の場合、メールアドレスは必須です。')
            if employee:
                raise forms.ValidationError('新規作成の場合、対象社員は指定できません。')
        elif action in ['update', 'delete']:
            if not employee:
                raise forms.ValidationError('更新/削除の場合、対象社員は必須です。')

        return cleaned_data
