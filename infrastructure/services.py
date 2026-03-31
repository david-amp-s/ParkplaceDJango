import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WeatherService:
    @staticmethod
    def get_clima_bogota():

        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=4.6097&longitude=-74.0817"
            "&current=temperature_2m,weathercode"
            "&timezone=America%2FBogota"
        )

        codigos = {
            0: "Despejado",
            1: "Mayormente despejado", 2: "Parcialmente nublado", 3: "Nublado",
            45: "Neblina", 48: "Neblina con escarcha",
            51: "Llovizna ligera", 53: "Llovizna moderada", 55: "Llovizna intensa",
            61: "Lluvia ligera", 63: "Lluvia moderada", 65: "Lluvia intensa",
            71: "Nieve ligera", 73: "Nieve moderada", 75: "Nieve intensa",
            80: "Chubascos ligeros", 81: "Chubascos moderados", 82: "Chubascos intensos",
            95: "Tormenta eléctrica", 96: "Tormenta con granizo", 99: "Tormenta fuerte",
        }

        try:
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                return "Servicio de clima no disponible"

            data = response.json()
            current = data.get('current', {})

            temp = current.get('temperature_2m', '--')
            codigo = current.get('weathercode', -1)
            desc = codigos.get(codigo, "Sin descripción")

            return f"{temp}°C - {desc}"

        except Exception as e:
            print(f"--- ERROR WEB SERVICE ---: {e}")
            return "Sin conexión al servicio de clima"