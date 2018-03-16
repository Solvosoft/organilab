'''
Created on 1/14/2018

@author: migue56
'''
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .utils import filters_params_api, get_valid_lab, get_response_code

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
            
                        
def get_json_room(self,lab,object_json):
    print ("get_json_room")
    
                
class LaboratoryRoomAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = LaboratoryRoom.objects.none()
    serializer_class = LaboratoryRoomSerializer
    
        
    def get (self,request,lab_pk):
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
    
    
    def get (self,request,lab_pk):
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
            self.queryset=  Furniture.objects.filter(labroom__laboratory=lab_pk).order_by('labroom')
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
            lab_room_serializer = FurnitureSerializer(data=request.data)
            if lab_room_serializer.is_valid():
                object=lab_room_serializer.save()
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
            self.queryset = Furniture.objects.filter(labroom__laboratory=lab_pk)
            room_furniture = get_object_furniture(self.queryset,pk)
            if room_furniture:
                room_furniture.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)     
        return get_response_code(status.HTTP_400_BAD_REQUEST)      
    
             
class ShelfAPIView(GenericAPIView):

    def get (self,request,lab_pk):    
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
        (lab,perm) = get_valid_lab(lab_pk,user,'laboratory.view_Shelf')
        
        if perm:
            self.queryset=  Furniture.objects.filter(labroom__laboratory=lab_pk).order_by('labroom')
            if params: # it can have filters params
                self.queryset=filters_params_api(self.queryset,params,Furniture)
                
            queryset = self.paginate_queryset(queryset=self.queryset)
        
            serialiser = FurnitureSerializer(instance=queryset, many=True)
            return self.get_paginated_response(serialiser.data)    
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