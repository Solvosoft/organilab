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
    row = serializers.IntegerField()
    col = serializers.IntegerField()

    class Meta:
        model = Shelf
        fields = '__all__' 
        
    def to_internal_value(self, data):
        data = super(ShelfSerializer, self).to_internal_value(data)
        
        print (data)
        return data
    
      
    def to_representation(self, instance):
            output = super(ShelfSerializer, self).to_representation(instance)
            (row,col) = instance.positions()
            output["row"]  = row
            output["col"] = col
            return output        
    
  
    
class ShelfObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelf
        fields = '__all__'
        
        
class ObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Object
        fields = '__all__'                
