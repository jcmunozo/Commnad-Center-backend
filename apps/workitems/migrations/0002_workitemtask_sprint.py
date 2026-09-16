import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0003_leavetype'),
        ('projects', '0010_sprint_and_task_sprint'),
        ('resources', '0005_teamworkloadperiod'),
        ('workitems', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalworkitemtask',
            name='sprint',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='projects.sprint'),
        ),
        migrations.AddField(
            model_name='workitemtask',
            name='sprint',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='work_item_tasks', to='projects.sprint'),
        ),
        migrations.AddIndex(
            model_name='workitemtask',
            index=models.Index(fields=['sprint'], name='work_item_t_sprint__bf2ea3_idx'),
        ),
    ]
