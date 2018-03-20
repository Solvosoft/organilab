from rest_framework.test import APIClient
from django.test import TestCase

import json

from django.contrib.auth.models import  User
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
    response = test.client.post(url,json.dumps(data))
    test.assertEqual(response.status_code,200) 
    token = response.data['token']       
    return token  
    
class TreeData(TestCase):
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
            laboratory = Laboratory.objects.create( 
                name= "Lab %i"%il,
                phone_number = '884665435'
            )   
        # ObjectFeatures    
        for i in range(count):
            of = ObjectFeatures.objects.create(
                  name= 'f%i'%i
                )          
        #objects
        for io in range(count):
            object = Object.objects.create( 
                code= "LBC-0003",
                name= "Ácido %i"%io,
                type= "0",
                description= "Corrosivo",
                molecular_formula= "H2SO4",
                cas_id_number= "7664-93-9",
                is_precursor= True,
                imdg_code= "8",
                #features= [of.pk]
            ) 
        # labroom
        for il in range(count):
            lab = LaboratoryRoom.objects.create( 
                name= "Sala %i"%il
                )
            laboratory.rooms.add(lab)
            # Furniture
            for ifu in range(count):
                ofurniture = Furniture.objects.create( 
                     name = "A-%i  Escritorio"%ifu,  
                     type= 'F',
                     dataconfig= "[]",
                     labroom= lab
                )               
                # Shelf
                for ish in range(count):
                    shelf = Shelf.objects.create( 
                         name = "Tapas cd-%i"%ish,  
                         type = "C",
                         furniture = ofurniture,
                         container_shelf =  None
                    )
                    # Shelfobject
                    for isho in range(count):
                        oshelf = ShelfObject.objects.create( 
                        quantity= 1,
                        limit_quantity= 0,
                        measurement_unit= "3",
                        shelf= shelf,
                        object= object
                        )        
        
                
class test_api_laboratoryroom(TreeData):
    
    def test_post(self):
        token=get_token(self)
        
        data = {"name":"Sala B4"}
        url='/api/4/rooms/'
        response=self.client.post(url, json.dumps(data),format="json")
        self.assertEqual(response.status_code,401)
        print (response.content)  
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(url,json.dumps(data),format="json",)
        self.assertEqual(response.status_code,201)               
        print (response.data)  
        
        
    def test_put(self):
        token=get_token(self)
        data ={"name":"Sala B4"}
        url='/api/4/rooms/1/'
        response = self.client.put(url,json.dumps(data), format="json")
        self.assertEqual(response.status_code,401)   
        print (response.data)       
        
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.put(url,json.dumps(data),format="json",)
        self.assertEqual(response.status_code,200)   
        print (response.data)  
    
     
    def test_get(self):
        token=get_token(self)
        url='/api/4/rooms/'
        response = self.client.get(url)
        self.assertEqual(response.status_code,401)   
        print (response.data)
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token) 
        response = self.client.get(url)
        self.assertEqual(response.status_code,200)   
        print (response.data)         
            
    def test_delete(self):
        token=get_token(self)
        url='/api/4/rooms/1/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code,401)   
        print (response.data)      
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.delete(url)
        self.assertEqual(response.status_code,204)   
        print (response.data)           
        
        
             
class test_api_furniture(TreeData):
    
    def test_post(self):
        token=get_token(self)      
        data = {
            "id": 66,
            "name": "A-13 Escritorio B",
            "type": "F",
            "dataconfig": "[[[], [387, 468]], [[465], [389, 392, 393]], [[], []]]",
            "labroom": 17
        }
        url='/api/4/furniture/'
        response=self.client.post(url, json.dumps(data),content_type="application/json")
        self.assertEqual(response.status_code,401)
        print (response.data)  
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(url,json.dumps(data),format='json')
        self.assertEqual(response.status_code,201)               
        print (response.data)  
        
        
    def test_put(self):
        token=get_token(self)
        data ={
            "id": 66,
            "name": "A-13 Escritorio B",
            "type": "F",
            "dataconfig": "[[],[]]",
            "labroom": 1
        }
        url='/api/4/furniture/1/'
        response = self.client.put(url,json.dumps(data),content_type="application/json")
        self.assertEqual(response.status_code,401)   
        print (response.data)       
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.put(url,json.dumps(data),format='json')
        self.assertEqual(response.status_code,200)   
        print (response.data)  
    
     
    def test_get(self):
        token=get_token(self)
        url='/api/4/furniture/'
        response = self.client.get(url)
        self.assertEqual(response.status_code,401)   
        print (response.data)
        
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(url,format='json')
        self.assertEqual(response.status_code,200)   
        print (response.data)         
            
    def test_delete(self):
        token=get_token(self)   
        url='/api/4/furniture/1/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code,401)   
        print (response.data)      
        
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code,204)   
        print (response.data)           
                