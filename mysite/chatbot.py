import openai
from django.conf import settings

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

def obtener_respuesta(mensaje_usuario):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres SeeleBot, un asistente de productividad alegre, motivador y empático. "
                    "Responde con entusiasmo, usando frases cortas, emojis si encajan bien y una estructura clara con saltos de línea o numeración. "
                    "Haz que las respuestas se sientan ligeras y motivadoras, evitando párrafos densos o demasiado técnicos. "
                    "Tu objetivo es animar, guiar y simplificar. Sé cálido y cercano."
                )
            },
            {"role": "user", "content": mensaje_usuario}
        ],
        max_tokens=400,
        temperature=0.8  # Puedes subirlo un poco para respuestas más creativas
    )

    return response.choices[0].message.content.strip()
