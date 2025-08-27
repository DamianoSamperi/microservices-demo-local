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
import requests
from io import BytesIO
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
    l.client.get("/product/" + random.choice(products),timeout=320)

def viewCart(l):
    l.client.get("/cart", timeout=320)

def addToCart(l):
    product = random.choice(products)
    l.client.get("/product/" + product,timeout=320)
    l.client.post(
        "/cart",
        json={
            'product_id': product,
            'quantity': random.randint(1, 10)
        },
        timeout=320
    )
def empty_cart(l):
    l.client.post('/cart/empty',timeout=320)

def checkout(l):
    addToCart(l)
    current_year = datetime.datetime.now().year + 1
    l.client.post(
        "/cart/checkout",
        json={
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
        },
        timeout=320
    )


def shoppingAssistant(l):
    prompts = [
        "Cerco un prodotto per l'estate",
        "Hai qualcosa per una camera da letto minimalista?",
        "Mi serve un tappeto in stile boho",
        "Sto arredando un ufficio elegante",
        "Cosa consigli per un bagno in stile naturale?"
    ]
    images = [
        None,
        "https://plus.unsplash.com/premium_photo-1676823547752-1d24e8597047?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "https://images.unsplash.com/photo-1615874959474-d609969a20ed?q=80&w=880&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        None,
        "https://images.unsplash.com/photo-1507652313519-d4e9174996dd?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    ]
    i = random.randint(0, len(prompts) - 1)
    payload = {
        "message": prompts[i]
    }
    if images[i]:
        payload["image"] = images[i]

    # l.client.post("/bot", json=payload)
    with l.client.post("/bot", json=payload, timeout=320,catch_response=True) as response:
        if response.status_code == 200:
            try:
                data = response.json()
                if "message" in data:
                    response.success()
                else:
                    response.failure(f"No 'message' in response: {data}")
            except Exception as e:
                response.failure(f"Invalid JSON: {e}")
        else:
            response.failure(f"HTTP {response.status_code}: {response.text}")


def addNewProduct(l):
    product_id = fake.uuid4()
    name = fake.word()
    description = fake.sentence()
    category = fake.word()
    price = round(random.uniform(10, 500), 2)

    # URL immagine remota
    image_url = "https://plus.unsplash.com/premium_photo-1664007654112-a6a19547ae7b?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"

    # Scarica l'immagine in memoria
    response = requests.get(image_url)
    response.raise_for_status()  # Controlla che abbia scaricato correttamente

    # Crea un file-like object in memoria
    img_file = BytesIO(response.content)

    files = {
        "image": ("image.jpg", img_file, "image/jpeg")
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
