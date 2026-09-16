import django.db.models.deletion
import simple_history.models
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0003_leavetype'),
        ('projects', '0009_remove_historicalproject_consumed_hours_and_more'),
        ('resources', '0005_teamworkloadperiod'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalSprint',
            fields=[
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(blank=True, db_index=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('custom_fields', models.JSONField(blank=True, default=dict)),
                ('name', models.CharField(max_length=100)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('CLOSED', 'Closed')], default='ACTIVE', max_length=10)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('created_by', models.ForeignKey(blank=True, db_constraint=False, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, db_constraint=False, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical sprint',
                'verbose_name_plural': 'historical sprints',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Sprint',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('custom_fields', models.JSONField(blank=True, default=dict)),
                ('name', models.CharField(max_length=100)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('CLOSED', 'Closed')], default='ACTIVE', max_length=10)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'sprint',
                'ordering': ['-start_date'],
            },
        ),
        migrations.AddField(
            model_name='historicaltask',
            name='sprint',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='projects.sprint'),
        ),
        migrations.AddField(
            model_name='task',
            name='sprint',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='projects.sprint'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['sprint'], name='task_sprint__5d955c_idx'),
        ),
        migrations.AddConstraint(
            model_name='sprint',
            constraint=models.UniqueConstraint(condition=models.Q(('status', 'ACTIVE')), fields=('status',), name='sprint_single_active'),
        ),
    ]
