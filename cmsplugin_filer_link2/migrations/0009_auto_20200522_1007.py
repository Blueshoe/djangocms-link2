# Generated by Django 2.2.12 on 2020-05-22 08:07

import cmsplugin_filer_link2.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cmsplugin_filer_link2', '0008_timeout_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filerlink2plugin',
            name='link_style',
            field=models.CharField(choices=[(' ', 'Default'), ('btn btn--primary btn--next', 'Gray Button'), ('btn btn--primaryBlue btn--next', 'Blue Button')], default=' ', max_length=255, verbose_name='link style'),
        ),
        migrations.AlterField(
            model_name='filerlink2plugin',
            name='page_link',
            field=cmsplugin_filer_link2.fields.Select2PageField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='cms.Page', verbose_name='page'),
        ),
    ]
