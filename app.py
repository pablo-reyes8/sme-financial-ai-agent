from flask import Flask, request, render_template_string
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
import bs4
from langchain_community.document_loaders import WebBaseLoader
import os
import certifi
import urllib3
import requests
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,)
import re
from markdown import markdown
from langchain.schema import BaseRetriever


app = Flask(__name__)
title = '💼 Asesor Financiero PYME'
subtitle = 'Tu agente personal para orientación financiera.'

# Historial inicial
messages = [
    {
        'sender': 'bot',
        'text': '¡Hola! Soy tu agente personal de finanzas para pymes. Estoy aquí para ayudarte con todas las dudas que tengas relacionadas sobre las finanzas de tu empresa. Cuéntame tu situación y objetivos, y comencemos.'
    }, 
    {
        'sender': 'bot',
        'text': 'Si deseas saber mas de mis funciones escribe Informacion...'
    }]

# Preguntas predeterminadas
quick_replies = [
    'Que impuestos debo pagar',
    'Cuales son los mejores creditos',
    'Que me recomiendas para mis finanzas']

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{{ title }}</title>

  <!-- ───────── Google Fonts (Inter) ───────── -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">

  <!-- ───────── MathJax (TeX → HTML) ───────── -->
  <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$','$']],
        displayMath: [['$$','$$'], ['\\[','\\]']]
      },
      svg: { fontCache: 'global' }
    };
  </script>
  <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>

  <style>
    /* ───────── GLOBAL ───────── */
    html {
      scroll-behavior: smooth;
    }
    :root{
      --page-bg:#FFFFFF; --container-bg:#FFFFFF; --text-color:#000000;
      --header-bg:#4E4376; --header-text:#FFFFFF;
      --header-hover-start:#6A5ACD; --header-hover-end:#4E4376;
      --user-bg:#375A35;   --user-text:#FFFFFF;
      --bot-bg:transparent; --bot-border:transparent;
      --qr-bg:#E4E6EA; --qr-text:#000000;
    }
    .dark-mode{
      --page-bg:#2C2C2C; --container-bg:#2C2C2C; --text-color:#DDDDDD;
      --header-bg:#333333; --header-text:#FFFFFF;
      --header-hover-start:#555555; --header-hover-end:#333333;
      --user-bg:#375A35;   --user-text:#FFFFFF;
      --bot-bg:transparent; --bot-border:transparent;
      --qr-bg:#3A3A3A; --qr-text:#FFFFFF;
    }
    *,*::before,*::after{box-sizing:border-box;}
    ::-webkit-scrollbar{width:9px;}
    ::-webkit-scrollbar-track{background:transparent;}
    ::-webkit-scrollbar-thumb{background:#AAAAAA;border-radius:5px;}
    .dark-mode ::-webkit-scrollbar-thumb{background:#555555;}

    body,html{
      margin:0;padding:0;height:100%;
      font-family:'Inter', sans-serif;
      background:var(--page-bg); color:var(--text-color);
      display:flex; flex-direction:column;
    }

    /* ───────── HEADER ───────── */
  header {
    position: fixed;
    top: 0; left: 0;
    width: 100%;
    background: var(--header-bg);
    color: var(--header-text);
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 10;
    overflow: hidden;            /* necesario para el ::before */
  }

  /* Pseudo-elemento que contiene el degradado */
  header::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(
      90deg,
      var(--header-hover-start),
      var(--header-hover-end)
    );
    opacity: 0;
    transition: opacity 0.5s ease-out;  /* salida suave */
    z-index: -1;                         /* detrás del contenido */
  }

  /* Efecto hover: entrada rápida */
  header:hover::before {
    opacity: 1;
    transition: opacity 0.2s ease-in;    /* entrada rápida */
  }

  /* Texto y switch dentro del header */
  header .title {
    font-size: 2rem;
    font-weight: bold;
  }
  header .subtitle {
    font-size: 1rem;
    font-weight: 500;
    opacity: .8;
    margin-left: 1rem;
  }
  .switch {
    position: relative;
    display: inline-block;
    width: 50px;
    height: 24px;
  }
  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  .slider {
    position: absolute;
    inset: 0;
    cursor: pointer;
    background: #ccc;
    border-radius: 24px;
    transition: .4s;
  }
  .slider:before {
    content: "";
    position: absolute;
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background: #fff;
    border-radius: 50%;
    transition: .4s;
  }
  input:checked + .slider {
    background: #2196F3;
  }
  input:checked + .slider:before {
    transform: translateX(26px);
  }

    /* ───────── ZONA DE MENSAJES ───────── */
    .content{
      flex:1; margin-top:120px; margin-bottom:100px;
      overflow-y:auto; padding:0 1rem;
    }
    .history{
      width:100%; max-width:900px; margin:0 auto;
      display:flex; flex-direction:column; gap:1rem;
      background:var(--container-bg); padding:1rem;
    }

    /* Fade-in animation para mensajes */
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .message-wrapper {
      display:flex; width:100%; align-items:flex-start;
      animation: fadeIn 0.2s ease-out;
    }
    .message-wrapper.user{ justify-content:flex-end; }

    .message{
      border-radius:12px; padding:.75rem 1rem;
    }
    .message.user{
      background:var(--user-bg); color:var(--user-text);
      max-width:70%;
    }
    .message.bot {
      background:var(--bot-bg); border:none; padding:0;
      color:var(--text-color); max-width:100%;
    }
    .message.bot p { white-space: pre-wrap; }

    /* ───────── TYPING INDICATOR ───────── */
    #typing-indicator { display:none; }
    #typing-indicator .dot{
      display:inline-block; width:6px; height:6px; margin:0 2px;
      background:var(--text-color); border-radius:50%;
      animation: blink 1s infinite;
    }
    #typing-indicator .dot:nth-child(2){ animation-delay:.2s; }
    #typing-indicator .dot:nth-child(3){ animation-delay:.4s; }
    @keyframes blink {
      0%,80%,100% { opacity:0; } 40% { opacity:1; }
    }

    /* ───────── CONTROLES ───────── */
    .controls{
      position:fixed; bottom:20px; left:50%; transform:translateX(-50%);
      width:100%; max-width:800px; display:flex; flex-direction:column;
      align-items:center; gap:.5rem;
    }
    .quick-replies{
      display:flex; gap:.5rem; flex-wrap:wrap;
      background:var(--qr-bg); padding:.5rem 1rem; border-radius:24px;
    }
    .qr-btn{
      background:var(--qr-bg); color:var(--qr-text); border:none;
      padding:.5rem 1rem; border-radius:16px; cursor:pointer;
      transition: transform .2s, background .2s;
    }
    .qr-btn:hover{
      transform:scale(1.05);
      background:var(--header-bg);
      color:var(--header-text);
    }
    form.input-area{
      display:flex; width:100%; background:var(--container-bg);
      border-radius:24px; padding:.5rem;
      box-shadow:0 2px 8px rgba(0,0,0,.1);
      transition: box-shadow .2s;
    }
    form.input-area:hover{
      box-shadow:0 4px 12px rgba(0,0,0,.15);
    }
    form.input-area textarea{
      flex:1; height:60px; resize:none; background:var(--container-bg);
      color:var(--text-color); border:1px solid var(--bot-border);
      border-radius:20px; padding:.5rem;
    }
    form.input-area textarea::placeholder{ color:#888; }
    form.input-area button{
      margin-left:.5rem; border-radius:20px;
      background:var(--header-bg); color:var(--header-text);
      border:none; padding:0 1.5rem; cursor:pointer;
      transition: transform .2s, background .2s;
    }
    form.input-area button:hover{
      transform:scale(1.05);
      background:var(--header-hover-start);
    }
  </style>
</head>

<body>
  <header>
    <div>
      <span class="title">{{ title }}</span>
      <span class="subtitle">{{ subtitle }}</span>
    </div>
    <div class="theme-switch">
      <label class="switch">
        <input type="checkbox" id="theme-toggle"><span class="slider"></span>
      </label>
    </div>
  </header>

  <div class="content">
    <div class="history">
      {% for msg in messages %}
        {% if msg.sender == 'bot' %}
          <div class="message-wrapper bot">
            <div class="message bot">{{ msg.text | safe }}</div>
          </div>
        {% else %}
          <div class="message-wrapper user">
            <div class="message user">{{ msg.text }}</div>
            <span class="avatar user">👤</span>
          </div>
        {% endif %}
      {% endfor %}

      <!-- Indicator de “escribiendo…” -->
      <div id="typing-indicator" class="message-wrapper bot">
        <div class="message bot">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>
    </div>
  </div>

  <div class="controls">
    {% if user_count < 1 %}
      <div class="quick-replies">
        {% for qr in quick_replies %}
          <button type="button" class="qr-btn">{{ qr }}</button>
        {% endfor %}
      </div>
    {% endif %}

    <form method="post" class="input-area">
      <textarea name="user_input" placeholder="Escribe tu consulta..."></textarea>
      <button type="submit">Enviar</button>
    </form>
  </div>

  <script>
    const textarea = document.querySelector('textarea[name="user_input"]');
    const form = document.querySelector('form.input-area');
    const toggle = document.getElementById('theme-toggle');
    const root = document.documentElement;
    const typingIndicator = document.getElementById('typing-indicator');

    textarea.addEventListener('keydown', e => {
      if (!e.shiftKey && e.key === 'Enter') {
        e.preventDefault();
        typingIndicator.style.display = 'flex';
        scrollToBottom();
        form.submit();
      }
    });

    document.querySelectorAll('.qr-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        textarea.value = btn.textContent;
        typingIndicator.style.display = 'flex';
        scrollToBottom();
        form.submit();
      });
    });

    toggle.addEventListener('change', () => {
      if (toggle.checked) {
        root.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
      } else {
        root.classList.remove('dark-mode');
        localStorage.setItem('theme', 'light');
      }
    });
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      root.classList.add('dark-mode');
      toggle.checked = true;
    }

    function scrollToBottom() {
      const content = document.querySelector('.content');
      content.scrollTop = content.scrollHeight;
    }
    window.addEventListener('load', scrollToBottom);
  </script>
</body>
</html>
"""

class CustomThresholdRetriever(BaseRetriever):
    vectorstore: Chroma   
    threshold: float = 0.3
    k: int = 4

    def _get_relevant_documents(self, query: str):
        docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=self.k)
        return [doc for doc, score in docs_and_scores if score < self.threshold]


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ["OPENAI_API_KEY"] = "Insert Your OpenAi Key"

session = requests.Session()
session.verify = False

loader = WebBaseLoader(
    web_paths=(
            "https://www.dian.gov.co/tramitesservicios/Paginas/adicionresponsabilidad42obligadollevarcontabilidad.aspx",
            "https://www.mincit.gov.co/servicio-ciudadano/preguntas-frecuentes/mipymes",
            "https://www.mincit.gov.co/minindustria/estrategia-transversal/formalizacion-empresarial",
            "https://www.ccb.org.co/services/create-your-company/establish-your-company/registration",
            "https://www.mincit.gov.co/getattachment/3a4e043d-98d3-40a8-ad9f-4160384088f3/Ley-590-de-2000-Por-la-cual-se-dictan-disposicione.aspx",
            "https://phylo.co/blog/obligaciones-legales-de-una-empresa-en-colombia/",
    ),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer("body")
    ),
    session=session)

docs = loader.load()

if not docs:
    raise RuntimeError("No se cargó ningún documento. Verifica las URLs y los selectores de BeautifulSoup.")
    
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)
    
non_empty_splits = [doc for doc in splits if doc.page_content and doc.page_content.strip()]
if not non_empty_splits:
    raise RuntimeError(
         "Tras el split no quedan chunks con contenido. "
        "Revisa tus selectores HTML o ajusta chunk_size/chunk_overlap.")

vectorstore = Chroma.from_documents(documents=non_empty_splits, embedding=OpenAIEmbeddings())
retriever = CustomThresholdRetriever(vectorstore=vectorstore, threshold=0.3, k=4)


system_prompt  = """
Eres “Asesor Financiero PyME COLOMBIANO”, un asistente especializado en finanzas, impuestos,
gestión operativa y desarrollo estratégico de pequeñas y medianas empresas para Colombia.
Tu objetivo es ofrecer orientación práctica, clara y accionable sobre esos temas.

════════════════  FORMATO DE RESPUESTA  ════════════════════ 
1. **Introducción**: un breve párrafo en texto corrido. (No escribas explicitamente **Introducción**)
2. **Pasos recomendados y parrafos sueltos:**  
   - Aquí sí usa viñetas (`- `).  
3. **Riesgos o Puntos de Atención:**  
   - Viñetas igualmente, pero **solo** en esta sección.
4.  Cronograma tentativo (SOLO EN CASO DE SUME VALOR A LA RESPUESTA)
  - escribelo igual que los **Riesgos o Puntos de Atención:**
5. **Cierre**: otro párrafo en texto corrido, invitando a profundizar. (No escribas explicitamente **Cierre**)

**No** incluyas saludos ni despedidas automáticas en cada respuesta 
Aplica las reglas de cortesía **solo** cuando el usuario inicie una despedida o un “gracias”.

════════════════  REGLAS DE CORTESÍA BÁSICA  ════════════════ 
• Despedida breve (ej. “adiós”, “nos vemos”) → «¡Hasta luego! Fue un placer ayudarte. ¡Que tengas un excelente día!»
• Agradecimiento simple (ej. “gracias”) → «¡El placer es mío! ¿Hay algo más en lo que pueda asistirte?»
• Pequeña charla casual (ej. “¿cómo estás?”) → responde brevemente («Muy bien, gracias»)
  y redirige con naturalidad: «¿En qué puedo apoyar tus finanzas hoy?»

**En los intercambios de cortesía no introduzcas información técnica ni documentos; responde brevemente y pregunta cómo ayudar en finanzas.**
** Tampoco escribas texto en formato latex ej: no escribas (informacion) o $informacion$**

════════════════  ALCANCE TEMÁTICO  ════════════════════════
• Si la pregunta es claramente sobre FINANZAS, BOLSA, ECONOMIA, ASESORIA FINANCIERA, IMPUESTOS, CONTABILIDAD,
  FINANCIACIÓN o GESTIÓN de PyMEs → sigue el Protocolo de Asesoría (abajo).
• Si la consulta es tangencial pero útil para PyMEs (p.ej. marketing, operaciones)
  puedes responder de forma general y relacionarlo con la rentabilidad o el flujo de caja.
• Si la consulta es totalmente ajena (p.ej. “qué es la mecánica cuántica”):
  1⃣ Responde cortésmente: «Ese tema está fuera de mi especialidad.»  
  2⃣ Invita a formular una duda dentro de tu ámbito: «Puedo ayudarte con asuntos
     financieros, contables o de gestión de PyMEs, si lo deseas.»

════════════════  PROTOCOLO DE ASESORÍA  ════════════════════
1. Busca en los documentos que se te pasaron y en tu propio conocimiento informacion para responder la pregunta 
2. Si faltan datos clave, formula preguntas concretas y numeradas.
3. Cuando dispongas de lo necesario, entrega un plan paso a paso que incluya:
     • Acciones recomendadas (bullets o numeradas)
     • Riesgos o puntos de atención
     • Cronograma tentativo con fechas o plazos (SOLO EN CASO DE SUME VALOR A LA RESPUESTA)

4. Mantén un tono cercano y profesional (3 a 9 líneas).  
   El usuario debe sentir que conversa con una persona empática y experta.
5. Cierra invitando a profundizar con frases variadas y pertinentes, por ejemplo:
   «¿Te gustaría que revisáramos los flujos de caja mes a mes?» o
   «Si necesitas más detalles sobre impuestos, dímelo y lo exploramos juntos».
6. No inventes datos ni regulaciones. Si no tienes certeza, indica
   «Conviene verificar esta información con la entidad oficial correspondiente».

(Usa estas reglas de forma flexible para mantener una conversación natural,
sin perder el enfoque en asesoría financiera para PyMEs.)
"""

prompt_template = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_prompt),
    # Aquí le decimos que inserte el historial:
    HumanMessagePromptTemplate.from_template("{chat_history}"),
    # Finalmente la entrada actual:
    HumanMessagePromptTemplate.from_template(
        "Pregunta: {question}\nContexto: {context}\nRespuesta:"
    ),])

memory = ConversationBufferWindowMemory(
    k=4,
    memory_key="chat_history",
    return_messages=True)

conv_chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.75),
    retriever=retriever,
    memory=memory,
    combine_docs_chain_kwargs={"prompt": prompt_template},
    return_source_documents=False,)

def clasificar(texto: str):
    txt = texto.lower().strip()
    if re.fullmatch(r"(hola|buenas|hey|qué tal)\b.*", txt):
        return "saludo"
    if re.fullmatch(r"(ad[ió]s|nos vemos|hasta luego)\b.*", txt):
        return "despedida"
    if re.fullmatch(r"(gracias|muchas gracias|mil gracias)\b.*", txt):
        return "agradecimiento"
    if re.fullmatch(r"(cómo estás|cómo te va|qué tal estás)\b.*", txt):
        return "smalltalk"
    return "consulta"


RESPUESTAS_RÁPIDAS = {
    "saludo":      "¡Hola! ¿En qué puedo ayudarte hoy con tus finanzas?",
    "despedida":   "¡Hasta luego! Fue un placer ayudarte. ¡Que tengas un excelente día!",
    "agradecimiento": "¡El placer es mío! ¿Hay algo más en lo que pueda asistirte?",
    "smalltalk":   "¡Muy bien, gracias! ¿En qué puedo apoyar tus finanzas hoy?"}

informacion = """\
Soy un **Agente Financiero PyME**, un asistente informativo diseñado para ofrecerte orientación práctica y actualizada sobre la gestión financiera de tu empresa, **sin necesidad de adjuntar documentos**.

Puedo ayudarte a:

- **Optimizar tu flujo de caja** con estrategias de cobranza, plazos de pago y control de inventarios.

- **Planificar tu carga impositiva** explicando calendarios de vencimientos, tarifas vigentes y posibles deducciones.

- **Analizar tus indicadores clave** liquidez, rentabilidad, endeudamiento y sugerir mejoras.

- **Explorar fuentes de financiamiento** créditos bancarios, leasing, inversionistas ángeles, crowdfunding.

- **Elaborar presupuestos y proyecciones** de ventas, gastos y resultados.

- **Estructurar tu política de precios y costos** para maximizar márgenes de utilidad.

- **Recomendar buenas prácticas** de contabilidad y control interno adaptadas a la normativa colombiana.

- **Asesorar en estrategias de crecimiento** reinversión de utilidades, diversificación de productos, alianzas.

Estoy aquí para resolver tus dudas y proporcionarte pasos concretos en cada tema. ¿Qué aspecto financiero de tu PyME te interesa abordar hoy?"""


@app.route('/', methods=['GET','POST'])
def index():
    if request.method == "GET":
        memory.clear()

    if request.method == "POST":
        text = request.form["user_input"].strip()
        messages.append({"sender": "user", "text": text})

        tipo = clasificar(text)

        if tipo != "consulta":
            raw = RESPUESTAS_RÁPIDAS[tipo]
        elif text.lower() == "informacion":
            raw = informacion
        else:
            raw = conv_chain({"question": text})["answer"]

        raw = raw.replace("\\(", "(").replace("\\)", ")")
        html = markdown(raw, extensions=["extra"])

        if text.lower() != "informacion":
          messages.append({"sender": "bot", "text": html})

    user_count = sum(1 for m in messages if m["sender"] == "user")
    return render_template_string(
        HTML,
        title=title,subtitle=subtitle,
        messages=messages,
        quick_replies=quick_replies,user_count=user_count,)

if __name__ == '__main__':
    app.run(debug=True)











