# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings


class EventLog(models.Model):
    '''
    shell scripts and views log their events here
    '''
    TEventID = models.AutoField(
        primary_key=True
    )
    TEvntTimeStamp = models.DateTimeField(
        "Time Stamp", auto_now_add=True
    )
    TEvntOwnr = models.CharField(
        "Owner", max_length=128
    )
    TEvntUser = models.CharField(
        "User", max_length=128
    )
    TEvntWrkStatn = models.CharField(
        "Work Station", max_length=128
    )
    TEvntGroup = models.CharField(
        "Group", max_length=128
    )
    TEvntDesc = models.TextField(
        "Description"
    )
    TEvntCmmnt = models.TextField(
        "Comments"
    )
    TEvntStatus = models.TextField(
        "Status"
    )
    TEvntStat01 = models.PositiveIntegerField(
        "Status 1",
        null=True, blank=True
    )
    TEvntStat02 = models.PositiveIntegerField(
        "Status 2",
        null=True, blank=True
    )
    TEvntStat03 = models.PositiveIntegerField(
        "Status 3"
    )

    def __unicode__(self):
        return "{}: {}".format(self.TEvntDesc, TEvntStatus)

    class Meta:
        db_table = "core_event_log"
        verbose_name = "Event Log"
        verbose_name_plural = "Event Log"
        ordering = ['-TEventID']
        get_latest_by = 'TEvntTimeStamp'
        indexes = [
            models.Index(
                fields=['TEvntTimeStamp'],
                name='tevent_time_stamp_idx'
            ),
            models.Index(
                fields=['TEvntOwnr'],
                name='tevent_owner_idx'
            ),
            models.Index(
                fields=['TEvntUser'],
                name='tevent_user_idx'
            ),
            models.Index(
                fields=['TEvntWrkStatn'],
                name='tevent_workstation_idx'
            ),
            models.Index(
                fields=['TEvntGroup'],
                name='tevent_group_idx'
            ),
            models.Index(
                fields=['TEvntStat01'],
                name='tevent_status_1_idx'
            ),
            models.Index(
                fields=['TEvntStat02'],
                name='tevent_status_2_idx'
            ),
            models.Index(
                fields=['TEvntStat03'],
                name='tevent_status_3_idx'
            ),
        ]
