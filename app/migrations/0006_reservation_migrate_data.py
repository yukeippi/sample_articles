# Generated migration for Reservation model

from uuid import uuid7

import django.db.models.deletion
from django.db import migrations, models


def migrate_department_reservations(apps, schema_editor):
    """既存のDepartmentReservationデータを新しいReservationモデルに移行"""
    DepartmentReservation = apps.get_model('app', 'DepartmentReservation')
    Reservation = apps.get_model('app', 'Reservation')
    Department = apps.get_model('app', 'Department')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # DepartmentのContentTypeを取得
    content_type = ContentType.objects.get_for_model(Department)

    # 既存のDepartmentReservationを新しいReservationに変換
    for dept_res in DepartmentReservation.objects.all():
        data = {}
        if dept_res.name:
            data['name'] = dept_res.name
        if dept_res.parent_id:
            data['parent_id'] = str(dept_res.parent_id)

        Reservation.objects.create(
            id=dept_res.id,
            content_type=content_type,
            object_id=dept_res.department_id,
            action=dept_res.action,
            data=data,
            scheduled_date=dept_res.scheduled_date,
            status_id=dept_res.status_id,
            created_at=dept_res.created_at,
            updated_at=dept_res.updated_at,
        )


def reverse_migration(apps, schema_editor):
    """ロールバック用（Reservationからデータを戻す）"""
    DepartmentReservation = apps.get_model('app', 'DepartmentReservation')
    Reservation = apps.get_model('app', 'Reservation')
    Department = apps.get_model('app', 'Department')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    content_type = ContentType.objects.get_for_model(Department)

    for reservation in Reservation.objects.filter(content_type=content_type):
        DepartmentReservation.objects.create(
            id=reservation.id,
            department_id=reservation.object_id,
            action=reservation.action,
            name=reservation.data.get('name'),
            parent_id=reservation.data.get('parent_id'),
            scheduled_date=reservation.scheduled_date,
            status_id=reservation.status_id,
            created_at=reservation.created_at,
            updated_at=reservation.updated_at,
        )


class Migration(migrations.Migration):
    dependencies = [
        ('app', '0005_add_update_status_data'),
        ('contenttypes', '__latest__'),
    ]

    operations = [
        # 新しいReservationモデルを作成
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                (
                    'id',
                    models.UUIDField(
                        default=uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'object_id',
                    models.UUIDField(
                        blank=True,
                        help_text='新規作成の場合はNull',
                        null=True,
                        verbose_name='対象オブジェクトID',
                    ),
                ),
                (
                    'action',
                    models.CharField(
                        choices=[('create', '新規作成'), ('update', '更新'), ('delete', '削除')],
                        max_length=10,
                        verbose_name='操作種別',
                    ),
                ),
                (
                    'data',
                    models.JSONField(
                        help_text='更新する内容をJSON形式で保存', verbose_name='更新データ'
                    ),
                ),
                ('scheduled_date', models.DateField(verbose_name='適用予定日')),
                (
                    'applied_at',
                    models.DateTimeField(blank=True, null=True, verbose_name='適用日時'),
                ),
                (
                    'applied_object_id',
                    models.UUIDField(
                        blank=True,
                        help_text='新規作成時に生成されたオブジェクトのID',
                        null=True,
                        verbose_name='適用後オブジェクトID',
                    ),
                ),
                (
                    'content_type',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='contenttypes.contenttype',
                        verbose_name='対象モデル',
                    ),
                ),
                (
                    'depends_on',
                    models.ForeignKey(
                        blank=True,
                        help_text='この予約の適用前に適用が必要な予約',
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='dependents',
                        to='app.reservation',
                        verbose_name='依存予約',
                    ),
                ),
                (
                    'status',
                    models.ForeignKey(
                        default='pending',
                        on_delete=django.db.models.deletion.PROTECT,
                        to='app.updatestatus',
                        verbose_name='ステータス',
                    ),
                ),
            ],
            options={
                'verbose_name': '予約更新',
                'verbose_name_plural': '予約更新',
                'ordering': ['scheduled_date', 'created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='reservation',
            index=models.Index(
                fields=['scheduled_date', 'status'], name='app_reserva_schedul_9c8e7e_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='reservation',
            index=models.Index(
                fields=['content_type', 'object_id'], name='app_reserva_content_f3a2d1_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='reservation',
            index=models.Index(fields=['depends_on'], name='app_reserva_depends_a1b2c3_idx'),
        ),
        # データ移行
        migrations.RunPython(migrate_department_reservations, reverse_migration),
        # 古いDepartmentReservationモデルを削除
        migrations.DeleteModel(
            name='DepartmentReservation',
        ),
    ]
