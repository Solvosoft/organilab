from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import TestCase
from django.urls import reverse

import json

from django.contrib.auth.models import  User
from .utils import list_shelf_dataconfig
from laboratory.models import (
    Laboratory,
    LaboratoryRoom, 
    Furniture,
    Shelf,
    ShelfObject,
    Object,
    ObjectFeatures
    )

def get_token(test):
    url = '/api/token-auth/'
    data={"username":"test","password":"test"}
    response = test.client.post(url,data,format="json")
    test.assertEqual(response.status_code,status.HTTP_200_OK) 
    token = response.data['token']     
    return token  
    
class TreeData(APITestCase):
    def setUp(self):
        self.user = User( 
             username='test',
             email="test@example.com",
             is_active=True,
             is_staff=True, 
             is_superuser=True
            )
        self.user.set_password('test')
        self.user.save()
        self.client= APIClient()
        
        count= 4
        # laboratory
        for il in range(count):
            laboratory = Laboratory ( 
                name= "Lab %i"%il,
                phone_number = '884665435'
            )
            laboratory.save()  
            self.lab=laboratory 
        # ObjectFeatures    
        for i in range(count):
            of = ObjectFeatures (
                  name= i
                )
            of.save()   
            self.feature=of       
        #objects
        for io in range(count):
            object = Object ( 
                code= "LBC-0003",
                name= "Ácido %i"%io,
                type= "0",
                description= "Corrosivo",
                molecular_formula= "H2SO4",
                cas_id_number= "7664-93-9",
                is_precursor= True,
                imdg_code= "8",
               
            ) 
            object.save()
            object.features.add(of)
            self.object=object
        # labroom
        for il in range(count):
            lab = LaboratoryRoom ( 
                name= "Sala %i"%il
                )
            lab.save()
            self.labroom=lab
            laboratory.rooms.add(lab)
            # Furniture
            for ifu in range(count):
                ofurniture = Furniture ( 
                     name = "A-%i  Escritorio"%ifu,  
                     type= 'F',
                     dataconfig= "[[[],[]]]",
                     labroom= lab
                ) 
                ofurniture.save()
                self.furniture=ofurniture              
                # Shelf
                for ish in range(count):
                    shelf = Shelf ( 
                         name = "Tapas cd-%i"%ish,  
                         type = "C",
                         furniture = ofurniture,
                         container_shelf =  None
                    )
                    shelf.save()
                    ofurniture.change_shelf_dataconfig(0,0,shelf.pk)
                    self.shelf=shelf
                    # Shelfobject
                    for isho in range(count):
                        oshelf = ShelfObject( 
                        quantity= 1,
                        limit_quantity= 0,
                        measurement_unit= "3",
                        shelf= shelf,
                        object= object
                        )   
                        oshelf.save() 
                        self.shelfO=oshelf    
        
                
class test_api_laboratoryroom(TreeData):
    
    def test_post(self):
        token=get_token(self)
        
        data = {"name":"Sala B4"}
        url="/api/%i/rooms/"%self.lab.pk
        response=self.client.post(url, data,format="json")
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)
           
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(url,data,format="json",)
        self.assertEqual(response.status_code,status.HTTP_201_CREATED)               
   
        
        
    def test_put(self):
        token=get_token(self)
        data ={"name":"Sala B4"}
        url="/api/%i/rooms/%i/"%(self.lab.pk,self.labroom.pk)
        
        response = self.client.put(url,data, format="json")
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
       
        
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.put(url,data,format="json",)
        self.assertEqual(response.status_code,status.HTTP_200_OK)    
    
     
    def test_get(self):
        token=get_token(self)
        url="/api/%i/rooms/"%self.lab.pk

        response = self.client.get(url)
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
         
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token) 
        response = self.client.get(url)
        self.assertEqual(response.status_code,status.HTTP_200_OK)   
        
            
    def test_delete(self):
        token=get_token(self)
        url="/api/%i/rooms/%i/"%(self.lab.pk,self.labroom.pk)
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
      
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.delete(url)
        self.assertEqual(response.status_code,status.HTTP_204_NO_CONTENT)   
                   
        
        
             
class test_api_furniture(TreeData):
    
    def test_post(self):
        token=get_token(self)      
        data = {
            "id": 66,
            "name": "A-13 Escritorio B",
            "type": "F",
            "dataconfig": "[[],[]]",
            "labroom":self.labroom.pk
        }
        url="/api/%i/furniture/"%(self.lab.pk)
        response=self.client.post(url, data,content_type="application/json")
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)
           
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(url,data,format='json')
        self.assertEqual(response.status_code,status.HTTP_201_CREATED)               
          
        
        
    def test_put(self):
        token=get_token(self)
        data ={
            "name": "A-13 Escritorio B",
            "type": "F",
            "dataconfig": "[[],[]]",
            "labroom": self.labroom.pk
        }
        url="/api/%i/furniture/%i/"%(self.lab.pk,self.furniture.pk)
        response = self.client.put(url,data,content_type="application/json")
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
       
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.put(url,data,format='json')
        self.assertEqual(response.status_code,status.HTTP_200_OK)   
          
    
     
    def test_get(self):
        token=get_token(self)
        url="/api/%i/furniture/"%(self.lab.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
         
        
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(url,format='json')
        self.assertEqual(response.status_code,status.HTTP_200_OK)   
                 
            
    def test_delete(self):
        token=get_token(self)   
        url="/api/%i/furniture/%i/"%(self.lab.pk,self.furniture.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
      
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code,status.HTTP_204_NO_CONTENT)   
            
        
        
        
                            
class test_api_Shelf(TreeData):
    
    def test_post(self):
        token=get_token(self)      
        data = {
            "name": "Tapas",
            "type": "C",
            "furniture":self.furniture.pk,
            "container_shelf": None,
            "row":0,
            "col":0
        }
        url="/api/%i/shelf/"%(self.lab.pk)
        response=self.client.post(url, data,content_type="application/json")
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)
           
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(url,data,format='json')               
        self.assertEqual(response.status_code,status.HTTP_201_CREATED)
        self.assertEqual(data['row'],response.data['row'])
        self.assertEqual(data['col'],response.data['col'])
        id = response.data['id']               
 
 
                 
        url="/api/%i/furniture/%i/"%(self.lab.pk,self.furniture.pk)        
        response = self.client.get(url,format='json')
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        
        # Shelf setting on dataconfig 
        listed =list_shelf_dataconfig(response.data['dataconfig'])
        self.assertTrue( (id in listed))    
                   
        
       
        
    def test_put(self):
        token=get_token(self)
        data = {
            "name": "Tapas",
            "type": "C",
            "furniture": self.furniture.pk,
            "container_shelf": None,
            "row":0,
            "col":1
        }
        url="/api/%i/shelf/%i/"%(self.lab.pk,self.shelf.pk)
        response = self.client.put(url,data,content_type="application/json")
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)       
       
        
        # bad count of row        
        data['row']=6
        url="/api/%i/shelf/%i/"%(self.lab.pk,self.shelf.pk)
        response = self.client.put(url,data,format='json')
        self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)   
        
        # good count of row  
        data['row']=0        
        response = self.client.put(url,data,format='json')
        self.assertEqual(response.status_code,status.HTTP_200_OK)  
          
         
        url="/api/%i/furniture/%i/"%(self.lab.pk,self.furniture.pk)        
        response = self.client.get(url,format='json')
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        
        # Shelf settingon dataconfig 
        listed =list_shelf_dataconfig(response.data['dataconfig'])
        self.assertTrue( (self.shelf.pk in listed))    
           
        

       
    def test_get(self):
        token=get_token(self)
        url="/api/%i/shelf/"%(self.lab.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
         
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(url,format='json')
        self.assertEqual(response.status_code,status.HTTP_200_OK)   
                 
            
    def test_delete(self):
        token=get_token(self)   
        url="/api/%i/shelf/%i/"%(self.lab.pk,self.shelf.pk)
        furniture_id=self.shelf.furniture.pk
        shelf_pk=self.shelf.pk
        
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
       
        
        # send to delete action
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code,status.HTTP_204_NO_CONTENT)   
        

        # check if shelf have been deleted
        response = self.client.get(url)
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)  
        
                
         # check changes on furniture dataconfig   
        url="/api/%i/furniture/%i/"%(self.lab.pk,furniture_id)        
        response = self.client.get(url,format='json')
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        
        # Shelf setting on dataconfig have been deleted
        listed =list_shelf_dataconfig(response.data['dataconfig'])
        self.assertTrue( (shelf_pk not in listed))          
           
        
                           
class test_api_ShelfObject(TreeData):
    
    def test_post(self):
        token=get_token(self)      
        data ={
            "quantity": 1,
            "limit_quantity": 0,
            "measurement_unit": "3",
            "shelf": self.shelf.pk,
            "object": self.object.pk
        }
        url="/api/%i/shelfobject/"%(self.lab.pk)
        response=self.client.post(url, data,content_type="application/json")
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)
           
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(url,data,format='json')
        self.assertEqual(response.status_code,status.HTTP_201_CREATED)               
          
        
        
    def test_put(self):
        token=get_token(self)
        data ={
            "quantity": 1,
            "limit_quantity": 0,
            "measurement_unit": "3",
            "shelf": self.shelf.pk,
            "object": self.object.pk
        }
        url="/api/%i/shelfobject/%i/"%(self.lab.pk,self.shelfO.pk)
        response = self.client.put(url,data,content_type="application/json")
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
       
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.put(url,data,format='json')   
        self.assertEqual(response.status_code,status.HTTP_200_OK)   
          
    
     
    def test_get(self):
        token=get_token(self)
        url="/api/%i/shelfobject/"%(self.lab.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
         
        
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(url,format='json')
        self.assertEqual(response.status_code,status.HTTP_200_OK)   
                 
            
    def test_delete(self):
        token=get_token(self)   
        url="/api/%i/shelfobject/%i/"%(self.lab.pk,self.shelfO.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
      
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code,status.HTTP_204_NO_CONTENT)   
           
            
                           
class test_api_Object(TreeData):
    
    def test_post(self):
        token=get_token(self)      
        data =  {
            "code": "LBC-0003",
            "name": "Ácido Sulfúrico",
            "type": "0",
            "description": "Corrosivo",
            "molecular_formula": "H2SO4",
            "cas_id_number": "7664-93-9",
            "is_precursor": True,
            "imdg_code": "8",
            'features': [self.feature.pk]            
        }
        url="/api/%i/object/"%(self.lab.pk)
        response=self.client.post(url, data,content_type="application/json")
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)
           
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        
        # Bad formule format
        data['molecular_formula']='XZ1ZX'
        response = self.client.post(url,data,format='json')
        self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST) 
        
        # Good formule format    
        data['molecular_formula']='H2SO4'            
        response = self.client.post(url,data,format='json')
        self.assertEqual(response.status_code,status.HTTP_201_CREATED)               
          
        
        
    def test_put(self):
        token=get_token(self)
        data = {
            "code": "LBC-0003",
            "name": "Ácido Sulfúrico",
            "type": "0",
            "description": "Corrosivo",
            "molecular_formula": "H2SO4",
            "cas_id_number": "7664-93-9",
            "is_precursor": True,
            "imdg_code": "8",
            'features': [self.feature.pk]
        }
        url="/api/%i/object/%i/"%(self.lab.pk,self.object.pk)
        response = self.client.put(url,data,content_type="application/json")
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
       
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        
        # Bad formule format
        data['molecular_formula']='XZ1ZX'
        response = self.client.put(url,data,format='json')
        self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)  
 
        # Good formule format
        data['molecular_formula']='H2SO4'
        response = self.client.put(url,data,format='json')
        self.assertEqual(response.status_code,status.HTTP_200_OK)            
    
     
    def test_get(self):
        token=get_token(self)
        url="/api/%i/object/"%(self.lab.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
         
        
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(url,format='json')
        self.assertEqual(response.status_code,status.HTTP_200_OK)   
                 
            
    def test_delete(self):
        token=get_token(self)   
        url="/api/%i/object/%i/"%(self.lab.pk,self.object.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)   
      
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code,status.HTTP_204_NO_CONTENT)   
                           