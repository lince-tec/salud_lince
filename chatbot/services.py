import unicodedata
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB


# =========================
# LIMPIEZA DE TEXTO
# =========================

def limpiar_texto(texto):
    if texto is None:
        return ""

    texto = str(texto).lower()

    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

    return texto.strip()


# =========================
# DATASET DE INTENCIONES
# =========================

intents_data = {

    "saludo": [
        "hola",
        "buenos dias",
        "que tal",
        "hey",
        "buen dia",
        "hola lincybot",
        "buenas tardes"
    ],

    "confirmacion": [
        "si",
        "sii",
        "claro",
        "por favor",
        "claro que si",
        "asi es"
    ],

    "despedida": [
        "adios",
        "gracias",
        "bye",
        "nos vemos",
        "hasta luego",
        "nada mas",
        "muchas gracias",
        "chao",
        "ok gracias",
        "terminar"
    ],

    "recuperar_password": [
        "olvide mi contrasena",
        "recuperar contraseña",
        "no puedo entrar",
        "perdi mi password",
        "restablecer contraseña",
        "no me se mi contraseña",
        "no recuerdo mi contraseña",
        "no puedo iniciar sesión",
        "no me deja entrar a mi cuenta"
    ],

    "cambiar_password": [
        "cambiar contraseña",
        "cambiar mi contraseña",
        "actualizar contraseña",
        "quiero otra contraseña",
        "cambiarla",
        "modificar password",
        "modificar mi contraseña"
    ],

    "ver_historial": [
        "ver historial",
        "mi expediente",
        "salud",
        "historial medico",
        "mi salud"
    ],

    "ver_consultas": [
        "mis consultas",
        "ver mis consultas",
        "mis citas",
        "consultas anteriores",
        "visitas"
    ],

    "agregar_contacto": [
        "agregar contacto",
        "numero de emergencia",
        "añadir telefono",
        "nuevo contacto",
        "números de contactos",
        "contacto de emergencia"
    ],

    "iniciar_sesion": [
        "ingresar",
        "acceder",
        "iniciar sesión",
        "iniciar sesion",
        "entrar",
        "quiero ingresar"
    ],

    "salir": [
        "salir",
        "quiero cerrar sesión",
        "cerrar sesion",
        "logout"
    ]
}


# =========================
# PREPARAR DATOS
# =========================

frases_entrenamiento = []
etiquetas = []

for intent, ejemplos in intents_data.items():

    for ejemplo in ejemplos:

        frases_entrenamiento.append(
            limpiar_texto(ejemplo)
        )

        etiquetas.append(intent)


# =========================
# STOPWORDS
# =========================

stopwords_es = [
    "de", "la", "que", "el", "en",
    "y", "a", "los", "del", "se",
    "las", "por", "un", "para",
    "con", "una", "su", "al",
    "lo", "como", "mas", "pero",
    "sus", "le", "ya", "o",
    "este", "porque", "esta",
    "entre", "cuando", "muy",
    "sin", "ok", "quiero"
]


# =========================
# VECTORIZACIÓN
# =========================

vectorizer = TfidfVectorizer(
    stop_words=stopwords_es,
    ngram_range=(1, 2)
)

X = vectorizer.fit_transform(frases_entrenamiento)


# =========================
# ENTRENAMIENTO
# =========================

clf = MultinomialNB()

clf.fit(X, etiquetas)


# =========================
# RESPUESTAS
# =========================

respuestas = {

    "saludo": "¡Hola! ¿En qué puedo ayudarte?",

    "confirmacion": "¿En qué puedo ayudarte?",

    "despedida": (
        "Espero haberte ayudado. "
        "Si necesitas algo más, aquí estaré para guiarte."
    ),

    "recuperar_password": (
        "Si no puedes entrar:\n"
        "1. Da clic en '¿Olvidaste tu contraseña?'\n"
        "2. Ingresa tu correo institucional.\n"
        "3. Sigue las instrucciones enviadas al correo."
    ),

    "cambiar_password": (
        "Para cambiar tu contraseña:\n"
        "1. Inicia sesión.\n"
        "2. Ve a Mi Perfil.\n"
        "3. Ingresa tu nueva contraseña."
    ),

    "ver_historial": (
        "Puedes consultar tu historial médico "
        "en la pestaña 'Historial médico'."
    ),

    "ver_consultas": (
        "Tus consultas están en el apartado "
        "'Mis Consultas'."
    ),

    "agregar_contacto": (
        "En 'Mi Perfil' encontrarás "
        "'Contactos de Emergencia'."
    ),

    "iniciar_sesion": (
        "Para iniciar sesión:\n"
        "1. Ingresa tu matrícula.\n"
        "2. Ingresa tu contraseña."
    ),

    "salir": (
        "Para cerrar sesión usa la opción "
        "'Salir'."
    )
}


# =========================
# FUNCIÓN PRINCIPAL
# =========================

def procesar_mensaje(
    mensaje,
    rol="invitado"
):

    texto_usuario = limpiar_texto(mensaje)

    if not texto_usuario:

        return {
            "respuesta": "El mensaje está vacío.",
            "intent": "vacio",
            "opciones": []
        }

    vec = vectorizer.transform([texto_usuario])

    probs = clf.predict_proba(vec)[0]

    confianza = np.max(probs)

    intent = clf.predict(vec)[0]

    opciones_default = [
        "Ver historial",
        "Cambiar contraseña",
        "Mis consultas",
        "Agregar contacto"
    ]

    intents_privados = [
        "ver_historial",
        "cambiar_password",
        "ver_consultas",
        "agregar_contacto"
    ]

    if (
        intent in intents_privados
        and rol != "paciente"
    ):

        return {
            "respuesta": (
                "Esta información solo está "
                "disponible para pacientes."
            ),
            "intent": "restriccion",
            "opciones": [
                "Iniciar sesión",
                "Recuperar contraseña"
            ]
        }

    if confianza < 0.15:

        return {
            "respuesta": (
                "No estoy seguro de entenderte."
            ),
            "intent": "desconocido",
            "opciones": opciones_default
        }

    return {
        "respuesta": respuestas.get(intent),
        "intent": intent,
        "opciones": (
            opciones_default
            if intent in ["saludo", "confirmacion"]
            else []
        )
    }