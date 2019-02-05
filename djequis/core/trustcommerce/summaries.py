
from django.db import models
from django.conf import settings
from django.db.models import CharField, Case, Value, When
from django.db.models import IntegerField, Sum

# class Transaction(models.Model):
#     2063 = 'Prk'
#     PRDV = 'Enr'
#     SOCCER = 'Scr'
#     CODE_CHOICES = (
#         (2063, 'Parking'),
#         (PRDV, 'Enrichment'),
#         (SOCCER, 'Soccer'),
#     )
#     name = models.CharField(max_length=50)
#     pcount = models.IntegerField()
#     choices=CODE_CHOICES
#     )
#
#     >>> # Create some more Clients first so we can have something to count
# 	Transaction.objects.create(
# 	    name='Parking',
# 	    account_type=Transaction.2063)
#     Transaction.objects.create(
#         name='Enrichment',
#         account_type=Transaction.PRDV)
#     Transaction.objects.create(
#         name='Soccer',
#         account_type=Transaction.SOCCER)
#
#     # Get counts for each value of account_type
#     Transaction.objects.aggregate(
#         prk=Sum(
#             Case(When(account_type=Transaction.2063, then=1),
#                  output_field=IntegerField())
#         ),
#         Enr=Sum(
#             Case(When(account_type=Transaction.PRDV, then=1),
#                  output_field=IntegerField())
#         ),
#         platinum=Sum(
#             Case(When(account_type=Transaction.SOCCER, then=1),
#                  output_field=IntegerField())
#         )
#     )

