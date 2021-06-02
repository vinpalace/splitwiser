from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class Group(models.Model):
    name = models.CharField(max_length=50)


class GroupMapping(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)


class Ledger(models.Model):
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='%(class)s_from_user')
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='%(class)s_to_user')
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    amount = models.IntegerField()
