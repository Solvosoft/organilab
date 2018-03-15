'''
Created on 1/142018

@author: migue56
'''
from rest_framework import serializers
from laboratory.models import (LaboratoryRoom, 
                               Furniture,
                               Shelf,
                               ShelfObject,
                               Object
                                )


class LaboratoryRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaboratoryRoom
        fields = '__all__'

class FurnitureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Furniture
        fields = '__all__'
        
        
class ShelfSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelf
        fields = '__all__'        
        
class ShelfObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelf
        fields = '__all__'
        
        
class ObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Object
        fields = '__all__'                