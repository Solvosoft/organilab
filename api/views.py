from django.shortcuts import render

from rest_framework.serializers import  Serializers
from rest_framework.generic import GenericAPIView
from rest_framework.respose import Response

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
    queryset = LaboratoryRoom.objects.all()
    serializer_class = LaboratoryRoomSerializer
    
    
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