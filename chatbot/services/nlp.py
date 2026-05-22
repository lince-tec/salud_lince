import unicodedata
import numpy as np
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from .intents import INTENTS

# Cargar modelo de español
try:
    nlp_sp = spacy.load("es_core_news_sm", disable=["ner", "parser"])
except:
    import os
    os.system("python -m spacy download es_core_news_sm")
    nlp_sp = spacy.load("es_core_news_sm")

def limpiar_texto_pro(texto):
    if not texto: return ""
    # Normalización
    texto = str(texto).lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn')
    # Lematización
    doc = nlp_sp(texto)
    return " ".join([token.lemma_ for token in doc if not token.is_punct]).strip()

# Preparar entrenamiento
frases_entrenamiento = []
etiquetas = []
for intent, ejemplos in INTENTS.items():
    for ej in ejemplos:
        frases_entrenamiento.append(limpiar_texto_pro(ej))
        etiquetas.append(intent)

# Vectorizador y Modelo
STOPWORDS_ES = ["de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para", "con"]

vectorizer = TfidfVectorizer(stop_words=STOPWORDS_ES, ngram_range=(1, 2), sublinear_tf=True)
X = vectorizer.fit_transform(frases_entrenamiento)
modelo = MultinomialNB(alpha=0.1).fit(X, etiquetas)

def predecir_intent(texto):
    texto_p = limpiar_texto_pro(texto)
    vec = vectorizer.transform([texto_p])
    probs = modelo.predict_proba(vec)[0]
    return modelo.predict(vec)[0], np.max(probs)