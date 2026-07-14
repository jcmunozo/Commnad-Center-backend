# Cliente == Trigger en este dominio (proxies API): antes de eliminar el FK
# client, preservamos el nombre del cliente como trigger_name donde falte.
from django.db import migrations


def copy_client_to_trigger(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    for project in Project.objects.select_related("client").filter(trigger_name=""):
        if project.client_id:
            project.trigger_name = project.client.name
            project.save(update_fields=["trigger_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0003_historicalproject_description_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_client_to_trigger, migrations.RunPython.noop),
    ]
