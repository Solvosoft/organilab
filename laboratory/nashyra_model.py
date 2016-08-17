'''
Created on 1/8/2016

@author: nashyra
'''
from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

@python_2_unicode_compatible
class LaboratoryRoom(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return '%s' % (self.name,)


@python_2_unicode_compatible
class Furniture(models.Model):
    labroom = models.ForeignKey(LaboratoryRoom)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=2)

    def __str__(self):
        return '%s' % (self.name,)

@python_2_unicode_compatible
class Shelf(models.Model):
    furniture = models.ForeignKey(Furniture)
    container_shelf = models.ForeignKey(null=True, blank=True)
    type = models.CharField(max_length=2)
    
    def __str__(self):
        return '%s' % (self.furniture,)
    

@python_2_unicode_compatible
class ObjectFeatures(models.Model):
    name = models.CharField(max_length=2)
    description = models.TextField()

    def __str__(self):
        return '%s' % (self.CHOICES[int(self.name)][1],)


class Object(models.Model):
    shelf = models.ForeignKey(Shelf)
    type = models.CharField(max_length=2)
    code = models.CharField(max_length=255)
    description = models.TextField()
    name = models.CharField(max_length=255)
    features = models.ManyToManyField(ObjectFeatures)

    def __str__(self):
        return '%s' % (self.name,)
