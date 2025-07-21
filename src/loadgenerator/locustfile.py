#!/usr/bin/python
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
from locust import FastHttpUser, TaskSet, between
from faker import Faker
import datetime
fake = Faker()

products = [
    '0PUK6V6EV0',
    '1YMWWN1N4O',
    '2ZYFJ3GM2N',
    '66VCHSJNUP',
    '6E92ZMYYFZ',
    '9SIQT8TOJO',
    'L9ECAV7KIM',
    'LS4PSXUNUM',
    'OLJCESPC7Z']

def index(l):
    l.client.get("/")

def setCurrency(l):
    currencies = ['EUR', 'USD', 'JPY', 'CAD', 'GBP', 'TRY']
    l.client.post("/setCurrency",
        {'currency_code': random.choice(currencies)})

def browseProduct(l):
    l.client.get("/product/" + random.choice(products))

def viewCart(l):
    l.client.get("/cart")

def addToCart(l):
    product = random.choice(products)
    l.client.get("/product/" + product)
    l.client.post("/cart", {
        'product_id': product,
        'quantity': random.randint(1,10)})
    
def empty_cart(l):
    l.client.post('/cart/empty')

def checkout(l):
    addToCart(l)
    current_year = datetime.datetime.now().year+1
    l.client.post("/cart/checkout", {
        'email': fake.email(),
        'street_address': fake.street_address(),
        'zip_code': fake.zipcode(),
        'city': fake.city(),
        'state': fake.state_abbr(),
        'country': fake.country(),
        'credit_card_number': fake.credit_card_number(card_type="visa"),
        'credit_card_expiration_month': random.randint(1, 12),
        'credit_card_expiration_year': random.randint(current_year, current_year + 70),
        'credit_card_cvv': f"{random.randint(100, 999)}",
    })

def shoppingAssistant(l):
    prompts = [
        "Cerco un divano moderno per il soggiorno",
        "Hai qualcosa per una camera da letto minimalista?",
        "Mi serve un tappeto in stile boho",
        "Sto arredando un ufficio elegante",
        "Cosa consigli per un bagno in stile naturale?"
    ]
    #images = [
    #    None,
    #    "https://example.com/images/living_room.jpg",
    #    "https://example.com/images/bedroom.jpg",
    #    None,
    #    "https://example.com/images/bathroom.jpg"
    #]
    images = [None]
    i = random.randint(0, len(prompts) - 1)
    payload = {
        "message": prompts[i]
    }
    if images[i]:
        payload["image"] = images[i]

    l.client.post("/assistant", json=payload)

def addNewProduct(l):
    product_id = fake.uuid4()
    name = fake.word()
    description = fake.sentence()
    category = fake.word()
    price = round(random.uniform(10, 500), 2)

    # Il path locale dell'immagine da caricare (assicurati che esista!)
    image_path = "./img/products/mug.jpg"

    # Apri l'immagine in modalità binaria
    with open(image_path, "rb") as img_file:
        files = {
            "image": ("mug.jpg", img_file, "image/jpeg")
        }
        data = {
            "name": name,
            "description": description,
            "price": str(price),
            "category": category
        }
        l.client.post("/add-product", data=data, files=files)


   
def logout(l):
    l.client.get('/logout')  


class UserBehavior(TaskSet):

    def on_start(self):
        index(self)

    tasks = {index: 1,
        setCurrency: 2,
        browseProduct: 10,
        addToCart: 2,
        viewCart: 3,
        checkout: 1, 
        shoppingAssistant: 4,
        addNewProduct: 2 }

class WebsiteUser(FastHttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 10)
