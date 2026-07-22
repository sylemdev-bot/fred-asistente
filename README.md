# Fred - Asistente personal por voz

Fred es un asistente de voz que hice en Python, inspirado en Jarvis. Escucha
por el micrófono, piensa las respuestas con IA (Gemini) y contesta hablando
con voz natural. Tiene personalidad de mayordomo, medio protector, como si
te tratara de hijo

## Qué hace

- Escucha y entiende lo que le dices en español
- Contesta hablando (voz de Edge TTS)
- Platica de lo que sea: consejos, matemáticas, trivia, charla normal
- Se acuerda de cosas si le dices "Fred, recuerda que..."
- Tiene una ventanita con un orbe que brilla cuando habla. Le das clic para pausar/reanudar el micrófono
- Dice el clima
- Abre YouTube, Google, Spotify, Xbox, Steam, Unity Hub
- Dice la hora y la fecha

## Instalación

Clona el repo:

git clone https://github.com/TU_USUARIO/fred-asistente.git
cd fred-asistente

Crea el entorno virtual (uso Python 3.12, con 3.14 me dio problemas de compatibilidad):

py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1

Instala lo necesario:

pip install -r requirements.txt


Crea un archivo `.env` con tu propia API key de Gemini (la sacas gratis en aistudio.google.com/apikey):

GEMINI_API_KEY=tu_api_key


Y ya, córrelo:

python fred.py


## Cómo usarlo

Le hablas diciendo su nombre primero:

- "Fred, qué hora es"
- "Fred, abre YouTube"
- "Fred, cómo está el clima"
- "Fred, recuerda que..."
- "Fred, dame un consejo"
- "Fred, adiós" (para apagarlo)

## Con qué está hecho

Python, SpeechRecognition, edge-tts, pygame, la API de Gemini y python-dotenv

## Pendientes

Todavía le falta activarse solo con "Hey Fred" sin tener que tocar nada,
y mejorar la voz. Sigo trabajando en eso
