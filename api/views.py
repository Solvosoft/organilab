'''
Created on 1/14/2018

@author: migue56
'''
from django.shortcuts import get_object_or_404

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .utils import filters_params_api, get_valid_lab

from .serializers import ( LaboratoryRoomSerializer,
                           FurnitureSerializer,
                           ShelfSerializer,
                           ShelfObjectSerializer,
                           ObjectSerializer
                           )
# models
from laboratory.models import (Laboratory,
                               LaboratoryRoom, 
                               Furniture,
                               Shelf,
                               ShelfObject,
                               Object
                                )

class LaboratoryRoomAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    
    queryset = LaboratoryRoom.objects.all()
    serializer_class = LaboratoryRoomSerializer
    
    
    def get (self,request,lab_pk, *arg,**kwargs):
        """
        Get:
        Use this to get your laboratoryrooms, to filter this result you can add query params to the url
        
        build your get whit your user token valid
         Header: [{"key":"Authorization","value":"Token  da293ee2561211f1edf5b6722f349a2e23898cbe"}]
         
        """
        params = request.query_params
        user = request.user
        lab = get_valid_lab(lab_pk,user,'laboratory.view_laboratoryroom')
        
        if lab:
              self.queryset= lab.rooms.all()     
        if params: # it can have filters params
            self.queryset=filters_params_api(self.queryset,params,LaboratoryRoom)
            
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