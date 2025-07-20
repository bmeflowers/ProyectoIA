import openai
from django.conf import settings

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

def obtener_respuesta(mensaje_usuario):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Eres un asistente de productividad inteligente."},
            {"role": "user", "content": mensaje_usuario}
        ],
        max_tokens=300,
        temperature=0.7
    )

    return response.choices[0].message.content.strip()
