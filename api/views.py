'''
Created on 1/14/2018

@author: migue56
'''
from django.shortcuts import render
from rest_framework.serializers import  Serializers
from rest_framework.generic import GenericAPIView
from rest_framework.respose import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

# Create your views here.
from laboratory.models import (LaboratoryRoom, 
                               Furniture,
                               Shelf,
                               ShelfObject,
                               Object
                                )
from .serializers import ( LaboratoryRoomSerializer,
                           FurnitureSerializer,
                           ShelfSerializer,
                           ShelfObjectSerializer,
                           ObjectSerializer
                           )

class LaboratoryRoomAPIView(GenericAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    
    queryset = LaboratoryRoom.objects.all()
    serializer_class = LaboratoryRoomSerializer
    
    
    def get (self,request,*arg,**kwargs):
        params = request.query_params
        if params: # when have a filters
            print (params)
            
        queryset = self.paginate_queryset(queryset=self.queryset)
        serialiser = LaboratoryRoomSerializer(instance=queryset, many=True)
        return self.get_paginated_response(serialiser.data)    
        
        
        
           
    
# class FurnitureAPIView(GenericAPIView):
#     
#     
#     
# class ShelfAPIView(GenericAPIView):
#     
#     
#     
#     
# class ShelfObjectAPIView(GenericAPIView):            
# 
# 
# 
# class ObjectAPIView(GenericAPIView):     