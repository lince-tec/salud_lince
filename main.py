import unicodedata
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np
from typing import Optional, List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def limpiar_texto(texto):
    if texto is None: return ""
    texto = str(texto).lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn')
    return texto.strip()

# --- 1. REFUERZO DE DATASET (Más ejemplos para palabras cortas) ---
intents_data = {
    "saludo": ["hola", "buenos dias", "que tal", "hey", "buen dia", "hola lincybot", "buenas tardes"],
    "confirmacion": ["si", "sii", "claro", "por favor", "claro que si", "asi es"],    
    "despedida": ["adios", "gracias", "bye", "nos vemos", "hasta luego", "nada mas", "muchas gracias", "chao", "ok gracias", "terminar"],
    "recuperar_password": ["olvide mi contrasena", "recuperar contraseña", "no puedo entrar", "perdi mi password", "restablecer contraseña", "no me se mi contraseña", "no recuerdo mi contraseña", "no puedo iniciar sesión", "no me deja entrar a mi cuenta"],
    "cambiar_password": ["cambiar contraseña","cambiar mi contraseña", "actualizar contraseña", "quiero otra contraseña", "cambiarla", "modificar password", "modificar mi contraseña"],
    "ver_historial": ["ver historial", "mi expediente", "salud", "historial medico", "mi salud"],
    "ver_consultas": ["mis consultas","ver mis consultas", "mis citas", "consultas anteriores", "visitas"],
    "agregar_contacto": ["agregar contacto", "numero de emergencia", "añadir telefono", "nuevo contacto", "números de contactos", "contacto de emergencia"],
    "iniciar_sesion": ["ingresar", "acceder", "iniciar sesión", "iniciar sesion", "entrar", "quiero ingresar"],
    "salir": ["salir", "quiero cerrar sesión", "cerrar sesion", "logout"]
}

frases_entrenamiento = []
etiquetas = []
for intent, ejemplos in intents_data.items():
    for ej in ejemplos:
        frases_entrenamiento.append(limpiar_texto(ej))
        etiquetas.append(intent)

# Mantenemos tus stopwords y el ngram_range
stopwords_es = ["de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para", "con", "una", "su", "al", "lo", "como", "mas", "pero", "sus", "le", "ya", "o", "este", "porque", "esta", "entre", "cuando", "muy", "sin", "ok", "quiero"]

vectorizer = TfidfVectorizer(stop_words=stopwords_es, ngram_range=(1,2))
X = vectorizer.fit_transform(frases_entrenamiento)
clf = MultinomialNB().fit(X, etiquetas)

respuestas = {
    "saludo": "¡Hola! ¿En qué puedo ayudarte?",
    "confirmacion": "¿En qué puedo ayudarte?",
    "despedida": "Espero haberte ayudado. Si necesitas algo más, aquí estaré para guiarte. Cuídate mucho y gracias por usar Salud Lince. ¡Hasta pronto!",
    "recuperar_password": "Si no puedes entrar: \n1. En el Login encontrarás el texto '¿Olvidaste tu contraseña?'. \n2. Da clic en él. \n3. Ingresa tu correo institucional. \n4. Sigue las instrucciones enviadas a tu correo.",
    "cambiar_password": "Para cambiar tu contraseña: \n1. Inicia sesión. \n2. Ve a 'Mi Perfil'. \n3. En la parte lateral derecha, ingresa tu contraseña actual y la nueva. \nTe recomiendo usar una contraseña segura.",
    "ver_historial": "Puedes consultar tu historial médico en la pestaña 'Historial médico' en la parte superior derecha.",
    "ver_consultas": "Tus consultas están en el apartado 'Mis Consultas' en la esquina superior derecha.",
    "agregar_contacto": "En 'Mi Perfil' (abajo a la izquierda) encontrarás 'Contactos de Emergencia'. \nTe recomiendo añadir al menos a una persona de confianza.",
    "iniciar_sesion": "Para iniciar sesión: \n1. Ingresa tu matrícula o número de trabajador. \n2. Ingresa tu contraseña enviada al correo institucional.",
    "salir": "Para cerrar sesión, usa la opción 'Salir' en la parte superior derecha."
}

class ChatRequest(BaseModel):
    mensaje: str
    esta_autenticado: bool
    rol: Optional[str] = "invitado"

@app.post("/lincybot/consultar")
async def consultar(request: ChatRequest):
    try:
        texto_usuario = limpiar_texto(request.mensaje)
        if not texto_usuario:
            return {"lincybot": "Parece que el mensaje está vacío.", "opciones": []}

        vec = vectorizer.transform([texto_usuario])
        probs = clf.predict_proba(vec)[0]
        confianza = np.max(probs)
        intent = clf.predict(vec)[0]

        opciones_default = ["Ver historial", "Cambiar contraseña", "Mis consultas", "Agregar contacto"]
        intents_privados = ["ver_historial", "cambiar_password", "ver_consultas", "agregar_contacto"]
        
        if intent in intents_privados and request.rol != "paciente":
            return {
                "lincybot": "Lo siento, esta información solo está disponible para pacientes registrados. Por favor, inicia sesión.",
                "opciones": ["Iniciar sesión", "Recuperar contraseña"],
                "intent": "restriccion"
            }

        # --- 2. UMBRAL AJUSTADO A 0.15 ---
        if confianza < 0.15:
            return {
                "lincybot": "No estoy seguro de entenderte. ¿Te refieres a alguna de estas opciones?",
                "opciones": opciones_default,
                "intent": "desconocido"
            }

        return {
            "lincybot": respuestas.get(intent),
            "opciones": opciones_default if intent in ["saludo", "confirmacion"] else [],
            "intent": intent
        }
    except Exception as e:
        return {"lincybot": f"Error técnico: {str(e)}", "opciones": []}