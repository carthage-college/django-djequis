from __future__ import unicode_literals

from django.db import models


class Acl(models.Model):
    principaltype = models.CharField(db_column='PrincipalType', max_length=25)
    principalid = models.IntegerField(db_column='PrincipalId')
    rightname = models.CharField(db_column='RightName', max_length=25)
    objecttype = models.CharField(db_column='ObjectType', max_length=25)
    objectid = models.IntegerField(db_column='ObjectId')
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ACL'


class Articles(models.Model):
    name = models.CharField(db_column='Name', max_length=255)
    summary = models.CharField(db_column='Summary', max_length=255)
    sortorder = models.IntegerField(db_column='SortOrder')
    # Field renamed because it was a Python reserved word.
    class_field = models.IntegerField(db_column='Class')
    parent = models.IntegerField(db_column='Parent')
    uri = models.CharField(db_column='URI', max_length=255, blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    disabled = models.IntegerField(db_column='Disabled')

    class Meta:
        managed = False
        db_table = 'Articles'


class Assets(models.Model):
    name = models.CharField(db_column='Name', max_length=255)
    catalog = models.IntegerField(db_column='Catalog')
    status = models.CharField(db_column='Status', max_length=64)
    description = models.CharField(db_column='Description', max_length=255)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Assets'


class Attributes(models.Model):
    name = models.CharField(db_column='Name', max_length=255, blank=True, null=True)
    description = models.CharField(db_column='Description', max_length=255, blank=True, null=True)
    content = models.TextField(db_column='Content', blank=True, null=True)
    contenttype = models.CharField(db_column='ContentType', max_length=16, blank=True, null=True)
    objecttype = models.CharField(db_column='ObjectType', max_length=64, blank=True, null=True)
    objectid = models.IntegerField(db_column='ObjectId', blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Attributes'


class Cachedgroupmembers(models.Model):
    groupid = models.IntegerField(db_column='GroupId', blank=True, null=True)
    memberid = models.IntegerField(db_column='MemberId', blank=True, null=True)
    via = models.IntegerField(db_column='Via', blank=True, null=True)
    immediateparentid = models.IntegerField(db_column='ImmediateParentId', blank=True, null=True)
    disabled = models.SmallIntegerField(db_column='Disabled')

    class Meta:
        managed = False
        db_table = 'CachedGroupMembers'


class Catalogs(models.Model):
    name = models.CharField(db_column='Name', max_length=255)
    lifecycle = models.CharField(db_column='Lifecycle', max_length=32)
    description = models.CharField(db_column='Description', max_length=255)
    disabled = models.SmallIntegerField(db_column='Disabled')
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Catalogs'


class Classes(models.Model):
    name = models.CharField(db_column='Name', max_length=255)
    description = models.CharField(db_column='Description', max_length=255)
    sortorder = models.IntegerField(db_column='SortOrder')
    disabled = models.IntegerField(db_column='Disabled')
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    hotlist = models.IntegerField(db_column='HotList')

    class Meta:
        managed = False
        db_table = 'Classes'


class Customfieldvalues(models.Model):
    customfield = models.IntegerField(db_column='CustomField')
    name = models.CharField(db_column='Name', max_length=200, blank=True, null=True)
    description = models.CharField(db_column='Description', max_length=255, blank=True, null=True)
    sortorder = models.IntegerField(db_column='SortOrder')
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    category = models.CharField(db_column='Category', max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'CustomFieldValues'


class Customfields(models.Model):
    name = models.CharField(db_column='Name', max_length=200, blank=True, null=True)
    type = models.CharField(db_column='Type', max_length=200, blank=True, null=True)
    maxvalues = models.IntegerField(db_column='MaxValues', blank=True, null=True)
    pattern = models.TextField(db_column='Pattern', blank=True, null=True)
    description = models.CharField(db_column='Description', max_length=255, blank=True, null=True)
    sortorder = models.IntegerField(db_column='SortOrder')
    lookuptype = models.CharField(db_column='LookupType', max_length=255)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    disabled = models.SmallIntegerField(db_column='Disabled')
    basedon = models.IntegerField(db_column='BasedOn', blank=True, null=True)
    rendertype = models.CharField(db_column='RenderType', max_length=64, blank=True, null=True)
    valuesclass = models.CharField(db_column='ValuesClass', max_length=64, blank=True, null=True)
    entryhint = models.CharField(db_column='EntryHint', max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'CustomFields'


class Customroles(models.Model):
    name = models.CharField(db_column='Name', max_length=200, blank=True, null=True)
    description = models.CharField(db_column='Description', max_length=255, blank=True, null=True)
    maxvalues = models.IntegerField(db_column='MaxValues', blank=True, null=True)
    entryhint = models.CharField(db_column='EntryHint', max_length=255, blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    disabled = models.SmallIntegerField(db_column='Disabled')

    class Meta:
        managed = False
        db_table = 'CustomRoles'


class FmArticles(models.Model):
    name = models.CharField(db_column='Name', max_length=255)
    summary = models.CharField(db_column='Summary', max_length=255)
    sortorder = models.IntegerField(db_column='SortOrder')
    # Field renamed because it was a Python reserved word.
    class_field = models.IntegerField(db_column='Class')
    parent = models.IntegerField(db_column='Parent')
    uri = models.CharField(db_column='URI', max_length=255, blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'FM_Articles'


class FmClasses(models.Model):
    name = models.CharField(db_column='Name', max_length=255)
    description = models.CharField(db_column='Description', max_length=255)
    sortorder = models.IntegerField(db_column='SortOrder')
    disabled = models.IntegerField(db_column='Disabled')
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    hotlist = models.IntegerField(db_column='HotList')

    class Meta:
        managed = False
        db_table = 'FM_Classes'


class FmObjecttopics(models.Model):
    topic = models.IntegerField(db_column='Topic')
    objecttype = models.CharField(db_column='ObjectType', max_length=64)
    objectid = models.IntegerField(db_column='ObjectId')

    class Meta:
        managed = False
        db_table = 'FM_ObjectTopics'


class FmTopics(models.Model):
    parent = models.IntegerField(db_column='Parent')
    name = models.CharField(db_column='Name', max_length=255)
    description = models.CharField(db_column='Description', max_length=255)
    objecttype = models.CharField(db_column='ObjectType', max_length=64)
    objectid = models.IntegerField(db_column='ObjectId')

    class Meta:
        managed = False
        db_table = 'FM_Topics'


class Groupmembers(models.Model):
    groupid = models.IntegerField(db_column='GroupId')
    memberid = models.IntegerField(db_column='MemberId')
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'GroupMembers'
        unique_together = (('groupid', 'memberid'),)


class Groups(models.Model):
    name = models.CharField(db_column='Name', max_length=200, blank=True, null=True)
    description = models.CharField(db_column='Description', max_length=255, blank=True, null=True)
    domain = models.CharField(db_column='Domain', max_length=64, blank=True, null=True)
    instance = models.IntegerField(db_column='Instance', blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Groups'


class Links(models.Model):
    base = models.CharField(db_column='Base', max_length=240, blank=True, null=True)
    target = models.CharField(db_column='Target', max_length=240, blank=True, null=True)
    type = models.CharField(db_column='Type', max_length=20)
    localtarget = models.IntegerField(db_column='LocalTarget')
    localbase = models.IntegerField(db_column='LocalBase')
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Links'


class Objectclasses(models.Model):
    # Field renamed because it was a Python reserved word.
    class_field = models.IntegerField(db_column='Class')
    objecttype = models.CharField(db_column='ObjectType', max_length=255)
    objectid = models.IntegerField(db_column='ObjectId')
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ObjectClasses'


class Objectcustomfieldvalues(models.Model):
    customfield = models.IntegerField(db_column='CustomField')
    objecttype = models.CharField(db_column='ObjectType', max_length=255)
    objectid = models.IntegerField(db_column='ObjectId')
    sortorder = models.IntegerField(db_column='SortOrder')
    content = models.CharField(db_column='Content', max_length=255, blank=True, null=True)
    largecontent = models.TextField(db_column='LargeContent', blank=True, null=True)
    contenttype = models.CharField(db_column='ContentType', max_length=80, blank=True, null=True)
    contentencoding = models.CharField(db_column='ContentEncoding', max_length=80, blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    disabled = models.SmallIntegerField(db_column='Disabled')

    class Meta:
        managed = False
        db_table = 'ObjectCustomFieldValues'


class Objectcustomfields(models.Model):
    customfield = models.IntegerField(db_column='CustomField')
    objectid = models.IntegerField(db_column='ObjectId')
    sortorder = models.IntegerField(db_column='SortOrder')
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ObjectCustomFields'


class Objectcustomroles(models.Model):
    customrole = models.IntegerField(db_column='CustomRole')
    objectid = models.IntegerField(db_column='ObjectId')
    sortorder = models.IntegerField(db_column='SortOrder')
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ObjectCustomRoles'
        unique_together = (('objectid', 'customrole'),)


class Objectscrips(models.Model):
    scrip = models.IntegerField(db_column='Scrip')
    stage = models.CharField(db_column='Stage', max_length=32)
    objectid = models.IntegerField(db_column='ObjectId')
    sortorder = models.IntegerField(db_column='SortOrder')
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ObjectScrips'
        unique_together = (('objectid', 'scrip'),)


class Objecttopics(models.Model):
    topic = models.IntegerField(db_column='Topic')
    objecttype = models.CharField(db_column='ObjectType', max_length=64)
    objectid = models.IntegerField(db_column='ObjectId')

    class Meta:
        managed = False
        db_table = 'ObjectTopics'


class Principals(models.Model):
    principaltype = models.CharField(db_column='PrincipalType', max_length=16)
    disabled = models.SmallIntegerField(db_column='Disabled')

    class Meta:
        managed = False
        db_table = 'Principals'


class Queues(models.Model):
    name = models.CharField(db_column='Name', unique=True, max_length=200)
    description = models.CharField(db_column='Description', max_length=255, blank=True, null=True)
    correspondaddress = models.CharField(db_column='CorrespondAddress', max_length=120, blank=True, null=True)
    commentaddress = models.CharField(db_column='CommentAddress', max_length=120, blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    disabled = models.SmallIntegerField(db_column='Disabled')
    subjecttag = models.CharField(db_column='SubjectTag', max_length=120, blank=True, null=True)
    lifecycle = models.CharField(db_column='Lifecycle', max_length=32, blank=True, null=True)
    sortorder = models.IntegerField(db_column='SortOrder')
    sladisabled = models.SmallIntegerField(db_column='SLADisabled')

    class Meta:
        managed = False
        db_table = 'Queues'


class Rtxassets(models.Model):
    name = models.CharField(db_column='Name', max_length=255)
    catalog = models.IntegerField(db_column='Catalog')
    status = models.CharField(db_column='Status', max_length=64)
    description = models.CharField(db_column='Description', max_length=255)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'RTxAssets'


class Rtxcatalogs(models.Model):
    name = models.CharField(db_column='Name', max_length=255)
    lifecycle = models.CharField(db_column='Lifecycle', max_length=32)
    description = models.CharField(db_column='Description', max_length=255)
    disabled = models.SmallIntegerField(db_column='Disabled')
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'RTxCatalogs'


class Scripactions(models.Model):
    name = models.CharField(db_column='Name', max_length=200, blank=True, null=True)
    description = models.CharField(db_column='Description', max_length=255, blank=True, null=True)
    execmodule = models.CharField(db_column='ExecModule', max_length=60, blank=True, null=True)
    argument = models.CharField(db_column='Argument', max_length=255, blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ScripActions'


class Scripconditions(models.Model):
    name = models.CharField(db_column='Name', max_length=200, blank=True, null=True)
    description = models.CharField(db_column='Description', max_length=255, blank=True, null=True)
    execmodule = models.CharField(db_column='ExecModule', max_length=60, blank=True, null=True)
    argument = models.CharField(db_column='Argument', max_length=255, blank=True, null=True)
    applicabletranstypes = models.CharField(db_column='ApplicableTransTypes', max_length=60, blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ScripConditions'


class Scrips(models.Model):
    description = models.CharField(db_column='Description', max_length=255, blank=True, null=True)
    scripcondition = models.IntegerField(db_column='ScripCondition')
    scripaction = models.IntegerField(db_column='ScripAction')
    customisapplicablecode = models.TextField(db_column='CustomIsApplicableCode', blank=True, null=True)
    custompreparecode = models.TextField(db_column='CustomPrepareCode', blank=True, null=True)
    customcommitcode = models.TextField(db_column='CustomCommitCode', blank=True, null=True)
    template = models.CharField(db_column='Template', max_length=200)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    disabled = models.SmallIntegerField(db_column='Disabled')

    class Meta:
        managed = False
        db_table = 'Scrips'


class Templates(models.Model):
    queue = models.IntegerField(db_column='Queue')
    name = models.CharField(db_column='Name', max_length=200)
    description = models.CharField(db_column='Description', max_length=255, blank=True, null=True)
    type = models.CharField(db_column='Type', max_length=16, blank=True, null=True)
    content = models.TextField(db_column='Content', blank=True, null=True)
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Templates'


class Tickets(models.Model):
    effectiveid = models.IntegerField(db_column='EffectiveId')
    queue = models.IntegerField(db_column='Queue')
    type = models.CharField(db_column='Type', max_length=16, blank=True, null=True)
    owner = models.IntegerField(db_column='Owner')
    subject = models.CharField(db_column='Subject', max_length=200, blank=True, null=True)
    initialpriority = models.IntegerField(db_column='InitialPriority')
    finalpriority = models.IntegerField(db_column='FinalPriority')
    priority = models.IntegerField(db_column='Priority')
    timeestimated = models.IntegerField(db_column='TimeEstimated')
    timeworked = models.IntegerField(db_column='TimeWorked')
    status = models.CharField(db_column='Status', max_length=64, blank=True, null=True)
    timeleft = models.IntegerField(db_column='TimeLeft')
    told = models.DateTimeField(db_column='Told', blank=True, null=True)
    starts = models.DateTimeField(db_column='Starts', blank=True, null=True)
    started = models.DateTimeField(db_column='Started', blank=True, null=True)
    due = models.DateTimeField(db_column='Due', blank=True, null=True)
    resolved = models.DateTimeField(db_column='Resolved', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    ismerged = models.SmallIntegerField(db_column='IsMerged', blank=True, null=True)
    sla = models.CharField(db_column='SLA', max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Tickets'


class Topics(models.Model):
    parent = models.IntegerField(db_column='Parent')
    name = models.CharField(db_column='Name', max_length=255)
    description = models.CharField(db_column='Description', max_length=255)
    objecttype = models.CharField(db_column='ObjectType', max_length=64)
    objectid = models.IntegerField(db_column='ObjectId')

    class Meta:
        managed = False
        db_table = 'Topics'


class Transactions(models.Model):
    objecttype = models.CharField(db_column='ObjectType', max_length=64)
    objectid = models.IntegerField(db_column='ObjectId')
    timetaken = models.IntegerField(db_column='TimeTaken')
    type = models.CharField(db_column='Type', max_length=20, blank=True, null=True)
    field = models.CharField(db_column='Field', max_length=40, blank=True, null=True)
    oldvalue = models.CharField(db_column='OldValue', max_length=255, blank=True, null=True)
    newvalue = models.CharField(db_column='NewValue', max_length=255, blank=True, null=True)
    referencetype = models.CharField(db_column='ReferenceType', max_length=255, blank=True, null=True)
    oldreference = models.IntegerField(db_column='OldReference', blank=True, null=True)
    newreference = models.IntegerField(db_column='NewReference', blank=True, null=True)
    data = models.CharField(db_column='Data', max_length=255, blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Transactions'


class Users(models.Model):
    name = models.CharField(db_column='Name', unique=True, max_length=200)
    password = models.CharField(db_column='Password', max_length=256, blank=True, null=True)
    comments = models.TextField(db_column='Comments', blank=True, null=True)
    signature = models.TextField(db_column='Signature', blank=True, null=True)
    emailaddress = models.CharField(db_column='EmailAddress', max_length=120, blank=True, null=True)
    freeformcontactinfo = models.TextField(db_column='FreeformContactInfo', blank=True, null=True)
    organization = models.CharField(db_column='Organization', max_length=200, blank=True, null=True)
    realname = models.CharField(db_column='RealName', max_length=120, blank=True, null=True)
    nickname = models.CharField(db_column='NickName', max_length=16, blank=True, null=True)
    lang = models.CharField(db_column='Lang', max_length=16, blank=True, null=True)
    gecos = models.CharField(db_column='Gecos', max_length=16, blank=True, null=True)
    homephone = models.CharField(db_column='HomePhone', max_length=30, blank=True, null=True)
    workphone = models.CharField(db_column='WorkPhone', max_length=30, blank=True, null=True)
    mobilephone = models.CharField(db_column='MobilePhone', max_length=30, blank=True, null=True)
    pagerphone = models.CharField(db_column='PagerPhone', max_length=30, blank=True, null=True)
    address1 = models.CharField(db_column='Address1', max_length=200, blank=True, null=True)
    address2 = models.CharField(db_column='Address2', max_length=200, blank=True, null=True)
    city = models.CharField(db_column='City', max_length=100, blank=True, null=True)
    state = models.CharField(db_column='State', max_length=100, blank=True, null=True)
    zip = models.CharField(db_column='Zip', max_length=16, blank=True, null=True)
    country = models.CharField(db_column='Country', max_length=50, blank=True, null=True)
    timezone = models.CharField(db_column='Timezone', max_length=50, blank=True, null=True)
    creator = models.IntegerField(db_column='Creator')
    created = models.DateTimeField(db_column='Created', blank=True, null=True)
    lastupdatedby = models.IntegerField(db_column='LastUpdatedBy')
    lastupdated = models.DateTimeField(db_column='LastUpdated', blank=True, null=True)
    authtoken = models.CharField(db_column='AuthToken', max_length=16, blank=True, null=True)
    smimecertificate = models.TextField(db_column='SMIMECertificate', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Users'
