'''
Created on 1/14/2018

@author: migue56
'''
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

# Utils
from .utils import filters_params_api, get_valid_lab, get_response_code
from laboratory.shelf_utils import get_dataconfig

# serializers
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
from django.core.serializers import serialize
def get_object_room(lab, pk):
    try:
        return lab.rooms.get(pk=pk)
    except LaboratoryRoom.DoesNotExist:
        get_response_code(status.HTTP_400_BAD_REQUEST)
        return LaboratoryRoom.objects.none()
            
def get_object_furniture(queryset, pk):
    try:
        return  queryset.filter(pk=pk).get()
    except LaboratoryRoom.DoesNotExist:
        get_response_code(status.HTTP_400_BAD_REQUEST)
        return Furniture.objects.none()
    
def get_object_shelf(furnitures,pk=None):
    try:
        if pk:
            return  Shelf.objects.filter(furniture__in=furnitures).filter(pk=pk).get()
        else:
            return Shelf.objects.filter(furniture__in=furnitures)      
    except Shelf.DoesNotExist:
        get_response_code(status.HTTP_400_BAD_REQUEST)
        return Shelf.objects.none()            
                        
def get_json_room(self,lab,object_json):
    print ("get_json_room")
    
                
class LaboratoryRoomAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = LaboratoryRoom.objects.none()
    serializer_class = LaboratoryRoomSerializer
    
        
    def get (self,request,lab_pk, pk = None):
        """
        Get:
        Use this to get your laboratoryrooms, to filter this result you can add query params to the url
        
        build your get with your user token valid
        
        Header: [{"key":"Authorization","value":"Token  a98fa58aacb028eb6aa83cd3ab8a827d919db399"},
               {"key":"Content-Type","value":"application/json","description":""}]
         
        URL filters: /api/4/rooms/?id=2  
        """
        params = request.query_params
        user = request.user
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.view_laboratoryroom')
        
        if perm:
            self.queryset= lab.rooms.all()  
            
            if pk:
                queryset=get_object_room(self.queryset,pk)
                serialiser = LaboratoryRoomSerializer(queryset)
                return Response(serialiser.data, status=status.HTTP_200_OK)
               
            if params: # it can have filters params
                self.queryset=filters_params_api(self.queryset,params,LaboratoryRoom)
                
            queryset = self.paginate_queryset(queryset=self.queryset)
        
            serialiser = LaboratoryRoomSerializer(instance=queryset, many=True)
            return self.get_paginated_response(serialiser.data)    
        return get_response_code(status.HTTP_400_BAD_REQUEST)
            
                    
           
    def put (self,request,lab_pk,pk):
        """
        Put:
        Use this to put to changes partial of laboratoryrooms
        
        build your put with your user token valid
        
        Header: [{"key":"Authorization","value":"Token  a98fa58aacb028eb6aa83cd3ab8a827d919db399"},
               {"key":"Content-Type","value":"application/json","description":""}]
        
        Body: {"id":18,"name":"Sala B4"}
         
        """
        user = request.user
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.change_laboratoryroom')
        if perm:
            lab_room = get_object_room_lab(lab,pk)
            if lab_room :
                serializer = LaboratoryRoomSerializer(lab_room,data=request.data)
                if serializer.is_valid():
                    serializer.save();
                    return Response (serializer.data)
                else: 
                     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return get_response_code(status.HTTP_400_BAD_REQUEST)     
        
            
           
    def post (self,request,lab_pk):
        """
        Post:
        Use this to create your laboratoryrooms
        
        build your post with your user token valid 
    
        Header: [{"key":"Authorization","value":"Token  a98fa58aacb028eb6aa83cd3ab8a827d919db399"},
               {"key":"Content-Type","value":"application/json","description":""}]
         
        Body: {"name":"Sala B4"} 
        """
        user = request.user
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.add_laboratoryroom')
        if perm:
            lab_room_serializer = LaboratoryRoomSerializer(data=request.data)
            if lab_room_serializer.is_valid():
                object=lab_room_serializer.save()
                lab.rooms.add(object)
                return Response(lab_room_serializer.data, status=status.HTTP_201_CREATED)
            else: 
                return Response(lab_room_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return get_response_code(status.HTTP_400_BAD_REQUEST)     
        
        
    def delete (self,request,lab_pk,pk):
        """
        Delete:
        Use this to delete your laboratoryrooms 
        
        build your delete with your user token valid 
        
        Header: [{"key":"Authorization","value":"Token  a98fa58aacb028eb6aa83cd3ab8a827d919db399"},
               {"key":"Content-Type","value":"application/json","description":""}]
         
        """
        user = request.user
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.delete_laboratoryroom')
        if perm:
            lab_room = get_object_room(lab,pk)
            if lab_room:
                lab_room.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)     
        return get_response_code(status.HTTP_400_BAD_REQUEST)   
                     
class FurnitureAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Furniture.objects.none()
    serializer_class = FurnitureSerializer
    
    
    def get (self,request,lab_pk,pk=None):
        """
        Get:
        Use this to get your Furniture, to filter this result you can add query params to the url
        
        build your get with your user token valid
        
        Header: [{"key":"Authorization","value":"Token  a98fa58aacb028eb6aa83cd3ab8a827d919db399"},
               {"key":"Content-Type","value":"application/json","description":""}]
        
        URL filters: /api/4/furniture/?id=2  
         
        """
        params = request.query_params
        user = request.user
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.view_furniture')
        
        if perm:
            self.queryset=  Furniture.objects.filter(
                labroom__laboratory=lab_pk).order_by('labroom')
                
            if pk:
                queryset=get_object_furniture(self.queryset,pk)
                serialiser = FurnitureSerializer(queryset)
                return Response(serialiser.data, status=status.HTTP_200_OK)
            
            if params: # it can have filters params
                self.queryset=filters_params_api(self.queryset,params,Furniture)
                
            queryset = self.paginate_queryset(queryset=self.queryset)
        
            serialiser = FurnitureSerializer(instance=queryset, many=True)
            return self.get_paginated_response(serialiser.data)    
        return get_response_code(status.HTTP_400_BAD_REQUEST)
    
    def put (self,request,lab_pk,pk):
        """
        Put:
        Use this to put to changes partial of Furniture
        
        build your put with your user token valid
        
        Header: [{"key":"Authorization","value":"Token  a98fa58aacb028eb6aa83cd3ab8a827d919db399"},
               {"key":"Content-Type","value":"application/json","description":""}]
        
        Body:{
            "name": "A-02 Gabinete azul de reactivos corrosivos M5",
            "type": "F",
            "dataconfig": "[[[332]],[[333]],[[334]],[[335]]]",
            "labroom": 17
            }
         
        """
        user = request.user
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.change_furniture')
        if perm:
            self.queryset = Furniture.objects.filter(labroom__laboratory=lab_pk)
            room_furniture = get_object_furniture(self.queryset,pk)
            if room_furniture :
                serializer = FurnitureSerializer(room_furniture,data=request.data)
                if serializer.is_valid():
                    serializer.save();
                    return Response (serializer.data)
                else: 
                     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return get_response_code(status.HTTP_400_BAD_REQUEST)     
    
    def post (self,request,lab_pk):
        """
        Post:
        Use this to create your Furniture
        
        build your post with your user token valid 
    
        Header: [{"key":"Authorization","value":"Token  a98fa58aacb028eb6aa83cd3ab8a827d919db399"},
               {"key":"Content-Type","value":"application/json","description":""}]
         
        Body: {
            "name": "A-02 Gabinete azul de reactivos corrosivos M5",
            "type": "F",
            "dataconfig": "[[[332]],[[333]],[[334]],[[335]]]",
            "labroom": 17
            }
        """
        user = request.user
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.add_furniture')
        if perm:
            serializer = FurnitureSerializer(data=request.data)
            if serializer.is_valid():
                object=serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else: 
                return Response(lab_room_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return get_response_code(status.HTTP_400_BAD_REQUEST)     
            
    def delete (self,request,lab_pk,pk):
        """
        Delete:
        Use this to delete your laboratoryrooms 
        
        build your delete with your user token valid 
        
        Header: [{"key":"Authorization","value":"Token  a98fa58aacb028eb6aa83cd3ab8a827d919db399"},
               {"key":"Content-Type","value":"application/json","description":""}]
         
        """
        user = request.user
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.delete_laboratoryroom')
        if perm:
            self.queryset = Furniture.objects.filter(labroom__laboratory=lab_pk)
            room_furniture = get_object_furniture(self.queryset,pk)
            if room_furniture:
                room_furniture.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)     
        return get_response_code(status.HTTP_400_BAD_REQUEST)      
    
             
class ShelfAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = ShelfSerializer
    queryset = Shelf.objects.none()

    def get (self,request,lab_pk,pk = None):    
        """
        Get:
        Use this to get your Shelf, to filter this result you can add query params to the url
        
        build your get with your user token valid
        
        Header: [{"key":"Authorization","value":"Token  a98fa58aacb028eb6aa83cd3ab8a827d919db399"},
               {"key":"Content-Type","value":"application/json","description":""}]
         
        URL filters: /api/4/shelf/?id=2  
        """
        params = request.query_params
        user = request.user
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.view_shelf')
        if perm:
            furnitures =  Furniture.objects.filter(labroom__laboratory=lab_pk
                                                   ).order_by('labroom'
                                                     ).values_list('id', flat=True)
            if pk:
                queryset=get_object_shelf(furnitures,pk)
                serialiser = ShelfSerializer(queryset)
                return Response(serialiser.data, status=status.HTTP_200_OK)
                
            self.queryset= get_object_shelf(furnitures)
            if params: # it can have filters params
                self.queryset=filters_params_api(self.queryset,params,Shelf)
                
            queryset = self.paginate_queryset(queryset=self.queryset)
        
            serialiser = ShelfSerializer(instance=queryset, many=True)
            return self.get_paginated_response(serialiser.data)    
        return get_response_code(status.HTTP_400_BAD_REQUEST) 
    
    def put (selfself,request,lab_pk,pk):
        """
        Put:
        Use this to create your shelf
        
        build your post with your user token valid 
    
        Header: [{"key":"Authorization","value":"Token  a98fa58aacb028eb6aa83cd3ab8a827d919db399"},
               {"key":"Content-Type","value":"application/json","description":""}]
         
        Body: {
            "name": "Tapas",
            "type": "D",
            "furniture": 64,
            "container_shelf": null
            }
        
        """       
        user = request.user
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.change_shelf')
        if perm:
            furnitures =  Furniture.objects.filter(labroom__laboratory=lab_pk
                                                   ).order_by('labroom'
                                                   ).values_list('id', flat=True)
            furniture_shelf = get_object_shelf(furnitures,pk)
            if furniture_shelf :
                serializer = ShelfSerializer(furniture_shelf,data=request.data)
                if serializer.is_valid():
                    serializer.save();
                    return Response (serializer.data)
                else: 
                     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return get_response_code(status.HTTP_400_BAD_REQUEST)     
          
    
    def post (selfself,request,lab_pk):
        """
        Post:
        Use this to create your shelf
        
        build your post with your user token valid 
    
        Header: [{"key":"Authorization","value":"Token  a98fa58aacb028eb6aa83cd3ab8a827d919db399"},
               {"key":"Content-Type","value":"application/json","description":""}]
         
        Body: 
        """            
        user = request.user
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.add_shelf')
        if perm:
            serializer = ShelfSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return response(serializer.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)        
        return get_response_code(status.HTTP_400_BAD_REQUEST)          
        
    def delete (self,request,lab_pk,pk):
        """
        Delete:
        Use this to delete your shelf 
        
        build your delete with your user token valid 
        
        Header: [{"key":"Authorization","value":"Token  a98fa58aacb028eb6aa83cd3ab8a827d919db399"},
               {"key":"Content-Type","value":"application/json","description":""}]
         
        """
        user = request.user
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.delete_laboratoryroom')
        if perm:
            furnitures =  Furniture.objects.filter(labroom__laboratory=lab_pk
                                                   ).order_by('labroom'
                                                   ).values_list('id', flat=True)
            furniture_shelf = get_object_shelf(furnitures,pk)
            if furniture_shelf:
                furniture_shelf.furniture.remove_shelf_dataconfig(pk)
                furniture_shelf.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)     
        return get_response_code(status.HTTP_400_BAD_REQUEST)           
#     
#     
#     
#     
# class ShelfObjectAPIView(GenericAPIView):            
# 
# 
# 
# class ObjectAPIView(GenericAPIView):     