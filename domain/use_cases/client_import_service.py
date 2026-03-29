import requests
from django.db import transaction
from infrastructure.models import Client

class ClientImportService:

    @staticmethod
    def import_from_java():

        url = "http://localhost:8080/api/datos"

        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            raise Exception("Error al consumir API")

        data = response.json()

        clients = []
        existing_phones = set(
            Client.objects.values_list('phone', flat=True)
        )

        for item in data:

            if not item.get("name") or not item.get("phone"):
                continue

            if item["phone"] in existing_phones:
                continue

            clients.append(Client(
                name=item["name"].strip(),
                phone=item["phone"].strip(),
                email=item.get("email")
            ))

        with transaction.atomic():
            Client.objects.bulk_create(clients)

        return len(clients)