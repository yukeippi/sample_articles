from django.db import migrations


def create_update_statuses(apps, schema_editor):
    """UpdateStatusマスターの初期データを作成"""
    UpdateStatus = apps.get_model('app', 'UpdateStatus')

    statuses = [
        {'code': 'pending', 'name': '予約中'},
        {'code': 'applied', 'name': '適用済み'},
        {'code': 'cancelled', 'name': 'キャンセル済み'},
    ]

    for status_data in statuses:
        UpdateStatus.objects.create(**status_data)


def delete_update_statuses(apps, schema_editor):
    """ロールバック用"""
    UpdateStatus = apps.get_model('app', 'UpdateStatus')
    UpdateStatus.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('app', '0004_updatestatus_organization_organizationreservation_and_more'),
    ]

    operations = [
        migrations.RunPython(create_update_statuses, delete_update_statuses),
    ]
