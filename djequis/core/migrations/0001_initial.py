# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-20 15:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EventLog',
            fields=[
                ('TEventID', models.IntegerField(primary_key=True, serialize=False)),
                ('TEvntTimeStamp', models.DateTimeField(auto_now_add=True, verbose_name=b'Time Stamp')),
                ('TEvntOwnr', models.CharField(max_length=128, verbose_name=b'Owner')),
                ('TEvntUser', models.CharField(max_length=128, verbose_name=b'User')),
                ('TEvntWrkStatn', models.CharField(max_length=128, verbose_name=b'Work Station')),
                ('TEvntGroup', models.CharField(max_length=128, verbose_name=b'Group')),
                ('TEvntDesc', models.TextField(verbose_name=b'Description')),
                ('TEvntCmmnt', models.TextField(verbose_name=b'Comments')),
                ('TEvntStatus', models.TextField(verbose_name=b'Status')),
                ('TEvntStat01', models.PositiveIntegerField(blank=True, null=True, verbose_name=b'Status 1')),
                ('TEvntStat02', models.PositiveIntegerField(blank=True, null=True, verbose_name=b'Status 2')),
                ('TEvntStat03', models.PositiveIntegerField(verbose_name=b'Status 3')),
            ],
            options={
                'get_latest_by': 'TEvntTimeStamp',
                'ordering': ['-TEventID'],
                'verbose_name_plural': 'Event Log',
                'db_table': 'core_event_log',
                'verbose_name': 'Event Log',
            },
        ),
        migrations.AddIndex(
            model_name='eventlog',
            index=models.Index(fields=[b'TEvntTimeStamp'], name='core_event__TEvntTi_3d3d25_idx'),
        ),
        migrations.AddIndex(
            model_name='eventlog',
            index=models.Index(fields=[b'TEvntOwnr'], name='core_event__TEvntOw_f48307_idx'),
        ),
        migrations.AddIndex(
            model_name='eventlog',
            index=models.Index(fields=[b'TEvntUser'], name='core_event__TEvntUs_f141b5_idx'),
        ),
        migrations.AddIndex(
            model_name='eventlog',
            index=models.Index(fields=[b'TEvntWrkStatn'], name='core_event__TEvntWr_a753df_idx'),
        ),
        migrations.AddIndex(
            model_name='eventlog',
            index=models.Index(fields=[b'TEvntGroup'], name='core_event__TEvntGr_b0169b_idx'),
        ),
        migrations.AddIndex(
            model_name='eventlog',
            index=models.Index(fields=[b'TEvntStat01'], name='core_event__TEvntSt_3f4516_idx'),
        ),
        migrations.AddIndex(
            model_name='eventlog',
            index=models.Index(fields=[b'TEvntStat02'], name='core_event__TEvntSt_c5f39d_idx'),
        ),
        migrations.AddIndex(
            model_name='eventlog',
            index=models.Index(fields=[b'TEvntStat03'], name='core_event__TEvntSt_06e544_idx'),
        ),
    ]
