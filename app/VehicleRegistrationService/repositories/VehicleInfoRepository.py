import random
import time
from faker import Faker

from models.VehicleInfo import VehicleInfo


class VehicleInfoRepository:
    def __init__(self):
        self._vehicle_brands = [
            "Mercedes", "Toyota", "Audi", "Volkswagen", "Seat", "Renault", "Skoda",
            "Kia", "Citroën", "Suzuki", "Mitsubishi", "Fiat", "Opel",
        ]

        self._models = {
            "Mercedes": ["A Class", "B Class", "C Class", "E Class", "SLS", "SLK"],
            "Toyota": ["Yaris", "Avensis", "Rav 4", "Prius", "Celica"],
            "Audi": ["A3", "A4", "A6", "A8", "Q5", "Q7"],
            "Volkswagen": ["Golf", "Pasat", "Tiguan", "Caddy"],
            "Seat": ["Leon", "Arona", "Ibiza", "Alhambra"],
            "Renault": ["Megane", "Clio", "Twingo", "Scenic", "Captur"],
            "Skoda": ["Octavia", "Fabia", "Superb", "Karoq", "Kodiaq"],
            "Kia": ["Picanto", "Rio", "Ceed", "XCeed", "Niro", "Sportage"],
            "Citroën": ["C1", "C2", "C3", "C4", "C4 Cactus", "Berlingo"],
            "Suzuki": ["Ignis", "Swift", "Vitara", "S-Cross", "Swace", "Jimny"],
            "Mitsubishi": ["Space Star", "ASX", "Eclipse Cross", "Outlander PHEV"],
            "Ford": ["Focus", "Ka", "C-Max", "Fusion", "Fiesta", "Mondeo", "Kuga"],
            "BMW": ["1 Serie", "2 Serie", "3 Serie", "5 Serie", "7 Serie", "X5"],
            "Fiat": ["500", "Panda", "Punto", "Tipo", "Multipla"],
            "Opel": ["Karl", "Corsa", "Astra", "Crossland X", "Insignia"],
        }

        self._rnd = random.Random()  # unseeded, like new Random()
        self._faker = Faker()

    def get(self, license_number: str) -> VehicleInfo:
        # simulate slow IO (5-200 ms)
        time.sleep(self._rnd.randint(5, 200) / 1000)

        # random vehicle info
        brand = self._get_random_brand()
        model = self._get_random_model(brand)

        # random owner info
        owner_name = f"{self._faker.first_name()} {self._faker.last_name()}"
        owner_email = owner_name.lower().replace(" ", ".") + "@outlook.com"

        return VehicleInfo(
            vehicleId=license_number,
            brand=brand,
            model=model,
            ownerName=owner_name,
            ownerEmail=owner_email,
        )

    def _get_random_brand(self) -> str:
        return self._rnd.choice(self._vehicle_brands)

    def _get_random_model(self, brand: str) -> str:
        return self._rnd.choice(self._models[brand])