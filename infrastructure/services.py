import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WeatherService:
    @staticmethod
    def get_clima_bogota():
        url = "https://wttr.in/Bogota?format=j1&lang=es"
        
        traducciones = {
            "Drizzle": "Llovizna",
            "Light drizzle": "Llovizna ligera",
            "Rain": "Lluvia",
            "Light rain": "Lluvia ligera",
            "Patchy rain nearby": "Lluvia dispersa cercana",
            "Cloudy": "Nublado",
            "Partly cloudy": "Parcialmente nublado",
            "Sunny": "Soleado",
            "Clear": "Despejado",
            "Overcast": "Muy nublado / Cubierto",
            "Mist": "Neblina",
            "Fog": "Niebla"
        }

        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                condicion = data['current_condition'][0]
                
                temp = condicion['temp_C']
                
                desc = ""
                if 'lang_es' in condicion and condicion['lang_es']:
                    desc = condicion['lang_es'][0]['value']
                elif 'weatherDesc' in condicion:
                    raw_desc = condicion['weatherDesc'][0]['value']
                    desc = traducciones.get(raw_desc, raw_desc)
                
                return f"{temp}°C - {desc}"
            
            return "Servicio de clima no disponible"
            
        except Exception as e:
            print(f"--- ERROR WEB SERVICE ---: {e}")
            return "Sin conexión al servicio de clima"