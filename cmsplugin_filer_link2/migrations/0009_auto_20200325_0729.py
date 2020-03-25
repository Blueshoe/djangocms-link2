# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-03-25 07:29
from __future__ import unicode_literals

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
            name='encrypt_mailto',
            field=models.BooleanField(default=True, help_text='Encrypt the mailto, as protection against bots collecting mails addresses.', verbose_name='Encryption of Mailto'),
        ),
        migrations.AlterField(
            model_name='filerlink2plugin',
            name='link_style',
            field=models.CharField(choices=[(' ', 'Default')], default=' ', max_length=255, verbose_name='link style'),
        ),
        migrations.AlterField(
            model_name='filerlink2plugin',
            name='page_link',
            field=cmsplugin_filer_link2.fields.Select2PageField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='cms.Page', verbose_name='page'),
        ),
    ]