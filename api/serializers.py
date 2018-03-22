'''
Created on 1/142018

@author: migue56
'''
import re
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from rest_framework import serializers
from .utils import list_shelf_dataconfig
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
        
    def to_internal_value(self, data):
        data = super(FurnitureSerializer, self).to_internal_value(data)
        
        id = data.get('id')
        dataconfig = data.get('dataconfig')
        
               
        if isinstance(dataconfig,str):
            #format regex valid
            match = re.search(r'^[\[\],\s"\d]*$',dataconfig)
            if not match:
                 raise serializers.ValidationError({ 'dataconfig': [_("Invalid format in shelf dataconfig ")] }) 
            
            # Can read the json format
            listed = list_shelf_dataconfig(dataconfig);
            if listed is False:
                raise serializers.ValidationError({ 'dataconfig': [_("Does not is decodable")] }) 
                        
            # data validation
            furniture_shelf_list = Shelf.objects.filter(pk__in=listed
                                                        ).filter(furniture__pk=id
                                                        ).values_list('pk',flat=True)
            for ipk in listed:
                if ipk not in furniture_shelf_list:
                     raise serializers.ValidationError(
                         { 'dataconfig': ["%i %s"%(ipk, _("Shelf does not is permitted"))] }
                     )
        elif isinstance(dataconfig,list):
            # Fix: add functions to process shelf  dataconfig like json
            print ("json")  
            
        return data

    def update(self,instance,validated_data):

        labroom = validated_data.get('labroom')
        
        if  labroom != instance.labroom :
            raise serializers.ValidationError({ 'labroom': [_("Laboratoryroom does not is changeable")] }) 

    
        return super(FurnitureSerializer, self).update(instance,validated_data)

        
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
            raise serializers.ValidationError({ 'col': ["col %i: %s"%(col, _("Invalid"))] })       
        row = data.get('row')
        if (row > furniture.get_row_count() or row < 0):
           raise serializers.ValidationError({ 'row': ["row %i: %s"%(row ,_("Invalid"))] })
        return data
    
    def create(self, validated_data):
        
        furniture = validated_data.get('furniture')
        col = validated_data.pop('col')
        row = validated_data.pop('row') 
                          
        object = Shelf.objects.create(**validated_data)
        furniture.change_shelf_dataconfig(row,col,object.pk)   
        
        return object
        
    def update(self,instance,validated_data):


        furniture = validated_data.get('furniture')
        
        if  furniture != instance.furniture :
            raise serializers.ValidationError({ 'furniture': [_("Furniture does not is changeable")] }) 
            
        
        col = validated_data.get('col')
        row = validated_data.get('row')             
        id = instance.pk
        
        furniture.change_shelf_dataconfig(row,col,id)       
        return super(ShelfSerializer, self).update(instance,validated_data)

      
    def to_representation(self, instance):
            output = super(ShelfSerializer, self).to_representation(instance)
            if hasattr(instance, 'furniture') :
              (row,col) = instance.positions()
            else: (row,col) = (None,None)  
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
        
        extra_kwargs = {'security_sheet': {'required': False}}

