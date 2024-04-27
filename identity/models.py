from django.db import models


class Customer(models.Model):
    LinkPrecedenceEnum = (('option1', 'primary'),('option2', 'secondary'))
    id = models.AutoField(primary_key=True)
    phoneNumber = models.CharField(max_length=10)
    email = models.CharField(max_length=255)
    linkedId = models.IntegerField(null=True)
    linkPrecedence = models.CharField(max_length=20, choices = LinkPrecedenceEnum, null = False)
    createdAt = models.DateTimeField()
    updatedAt = models.DateTimeField()
    deletedAt = models.DateTimeField(null=True,default = None)