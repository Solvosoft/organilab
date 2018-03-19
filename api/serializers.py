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
        furniture = data.get('furniture')
        
        col = data.get('col')
        if (col > furniture.get_col_count()  or col < 0):
            raise serializers.ValidationError({ 'col': ["col %i not exist "%col] })       
        row = data.get('row')
        if (row > furniture.get_row_count() or row < 0):
           raise serializers.ValidationError({ 'row': ["row %i not exist "%row] })
        return data
    
    def create(self, validated_data):
        furniture = validated_data.get('furniture')
        col = validated_data.get('col')
        row = validated_data.get('row')             
        id = instance.pk
        
        furniture.change_shelf_dataconfig(row,col,id)               
    
        return Comment.objects.create(**validated_data)
        
    def update(self,instance,validated_data):
        print(validated_data)
        furniture = validated_data.get('furniture')
        col = validated_data.get('col')
        row = validated_data.get('row')             
        id = instance.pk
        
        furniture.change_shelf_dataconfig(row,col,id)       
        return super(ShelfSerializer, self).update(instance,validated_data)

      
    def to_representation(self, instance):
            output = super(ShelfSerializer, self).to_representation(instance)
            (row,col) = instance.positions()
            output["row"]  = row
            output["col"] = col
            return output        
    
    def get_row(self,instance):
        return instance.row()
        
    def get_col(self,instance):
        return instance.col()
      
    
class ShelfObjectSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ShelfObject
        fields = '__all__'
            
        
class ObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Object
        fields = '__all__' 
        
        extra_kwargs = {
            'security_sheet': {'read_only': True},
        }               
