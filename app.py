from io import BytesIO
import streamlit as st
import base64
import time
import numpy as np
import pickle
import faiss
from sentence_transformers import SentenceTransformer
import requests
import json
import ast
import re
from openai import OpenAI

# Configure page
st.set_page_config(
    page_title="روبوت محادثة قانوني مدعوم بالذكاء الاصطناعي",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def load_models():
    """Load embedding model, FAISS index and metadata"""
    try:
        # Load embedding model
        embedding_model = SentenceTransformer('./output/embedding_model')  # Remplacez par votre modèle
        
        # Load FAISS index
        faiss_index = faiss.read_index('./output/faiss_index.idx')
        
        # Load metadata
        with open('./output/faiss_metadata.pkl', 'rb') as f:
            metadata = pickle.load(f)
        
        return embedding_model, faiss_index, metadata
    except Exception as e:
        st.error(f"Erreur lors du chargement des modèles: {e}")
        return None, None, None

CHATGPT_APLI_KEY = ""  
client = OpenAI(api_key=CHATGPT_APLI_KEY)

def call_gpt3 (messages, temperature=0.3, max_tokens=1024):
    response = client.chat.completions.create(
        model="gpt-4o",
        # model="gpt-3.5-turbo",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


OPENROUTER_API_KEY = ""  
def call_deepseek_v3(messages, temperature=0.7, max_tokens=1000):
    """Call DeepSeek V3 via OpenRouter API"""
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://kaggle.com",  
        "X-Title": "Legal RAG Assistant",    
    }
    
    data = {
        "model": "deepseek/deepseek-chat-v3-0324:free", 
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  
        
        result = response.json()
        return result['choices'][0]['message']['content']
        
    except requests.exceptions.RequestException as e:
        return f"API Request Error: {str(e)}"
    except KeyError as e:
        return f"Response Parse Error: {str(e)}"
    except Exception as e:
        return f"Unexpected Error: {str(e)}"

def detect_language(text):
    """Detects if text is Arabic (RTL)"""
    return bool(re.search('[\u0600-\u06FF\u0750-\u077F]', text))


def translate_to_french(text):
    is_arabic = detect_language(text)
    # Get the translation
    messages = [
        {
            "role": "system",
            "content": "You are a translator. Translate the given text to French. ONLY return the translation, nothing else!"
        },
        {
            "role": "user", 
            "content": f"Translate this to French: {text}"
        }
    ]

    # response = call_gpt3(messages)
    response = call_deepseek_v3(messages)
    
    return response, is_arabic

def is_no_information_response(response):
    """Check if the response indicates no sufficient information"""
    no_info_indicators = [
        "je ne dispose pas d'informations suffisantes",
        "i don't have enough information", 
        "لا أملك معلومات كافية",
        "pas d'informations suffisantes",
        "not enough information",
        "insufficient information",
        "no sufficient information"
    ]
    
    response_lower = response.lower()
    return any(indicator in response_lower for indicator in no_info_indicators)

def advanced_rag_query(query, top_k=5):
    """Advanced RAG with language detection and strict context-only responses"""
    
    # Store original query for language detection
    original_query = query
    
    # Translate query to French for embedding consistency
    french_query, original_lang = translate_to_french(query)
    # Retrieve documents using French query
    query_embedding = embedding_model.encode([french_query])
    query_embedding = np.array(query_embedding).astype('float32')
    scores, indices = faiss_index.search(query_embedding, top_k)
    
    # Format context with document numbering
    context_parts = []
    for i, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
        if idx != -1:
            doc_text = metadata[idx]
            context_parts.append(f"Document {i}:\n{doc_text}")
    
    context = "\n\n".join(context_parts)

    document_ids = []
    for ctx in context_parts:
        element = ctx.split('\n')
        element = ast.literal_eval(element[-1])
        for ele in element:
            document_ids.append(ele['doc_id'])
    
    html_links = ""
    for i, doc_id in enumerate(document_ids):
        year = doc_id[1:5]
        number = str(int(doc_id[5:]))  # remove leading zeros
        title = f"- المستند {i}: الجريدة الرسمية رقم {number} عام {year}"
        url = f"https://www.joradp.dz/FTP/JO-FRANCAIS/{year}/{doc_id}.pdf"
        html_links += f'<br>{title}: <a href="{url}" target="_blank">{url}</a>'


    prompt = f"""You are a legal assistant expert. Answer the user's question using ONLY the information provided in the documents below and with the same LANGUAGE as the user's question. 

IMPORTANT INSTRUCTIONS:
- Respond in the SAME LANGUAGE as this {original_query} question's language
- Use ONLY information from the provided documents
- DO NOT use your general knowledge or training data, if the answer is not mentioned in the CONTEXT DOCUMENTS say that i do not have enogh inforamation
- Reference specific documents in the end of the answer with a title is Sources:
- DO NOT list or include a source section at the end of your answer

CONTEXT DOCUMENTS provided:
{context}

USER QUESTION: {original_query}

CONSTRAINTS:
- Answer language: Same as the question language
- Information source: Only the provided documents above

ANSWER:"""

    messages = [
        {
            "role": "system", 
            "content": "You are a legal assistant. You must respond in the same language as the user's question and use ONLY the information from the provided context documents. Never use your general knowledge."
        },
        {
            "role": "user", 
            "content": prompt
        }
    ]

    # response = call_gpt3(messages)
    response = call_deepseek_v3(messages)

    if is_no_information_response(response):
        return None
    
    return response, html_links, original_lang

embedding_model, faiss_index, metadata = load_models()

if embedding_model is None:
    st.error("يرجى المحاولة مجددا")
    st.stop()




# Custom CSS for Arabic RTL layout and styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@200;300;400;500;700;800;900&display=swap');
    
    * {
        font-family: "Tajawal", sans-serif;
    }
    
    .main {
        direction: rtl;
        text-align: right;
    }
    
    .header-container {
        background: #EAEAEA;
        padding: 15px 0 0;
        margin: 0;
        border-radius: 0;
    }
    
    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 94%;
        margin: 0 auto 16px;
        padding: 0 20px;
    }
    
    .title-container {
        text-align: center;
        flex-grow: 1;
    }
    
    .main-title {
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 5px;
        color: #1D5038;
    }
    
    .sub-title {
        font-size: 32px;
        color: #D21033;
        font-weight: 800;
    }
    
    .language-selector {
        background-color: #006636;
        width: 100%;
        color: white;
        padding: 8px 50px;
        text-align: end;
        font-size: 14px;
        margin-top: 5px;
        padding-right: 75px;
    }
    
    .chat-heading {
        color: #D21033;
        font-size: 30px;
        margin: 120px 0 40px;
        font-weight: 800;
        text-align: center;
    }
    
    .user-message {
        background-color: #ECECEC;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        max-width: fit-content;
        font-size: 16px;
        font-weight: 500;
        direction: rtl;
        text-align: right;
        margin: 30px auto 15px 80px;
    }
    
    .bot-message {
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        max-width: 80%;
        margin: auto;
    }
    
    .response-title {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        color: #000;
        font-weight: 700;
        font-size: 24px;
        direction: rtl;
    }
    
    .title-icon {
        margin-left: 10px;
        font-size: 24px;
    }
    
    .message-content {
        margin-bottom: 10px;
        font-size: 16px;
        font-weight: 400;
        color: #000;
        line-height: 1.6;
    }
    
    .message-content ul {
        margin: 10px 0;
        padding-right: 20px;
    }
    
    .message-content li {
        margin-bottom: 8px;
        line-height: 1.5;
    }
    
    .info-source {
        font-size: 14px;
        color: #666;
        margin-top: 10px;
        padding-bottom: 80px;
        direction: rtl;
        text-align: right;
    }
    
    .info-source a {
        color: #1D5038;
        text-decoration: underline;
    }
    
    .stTextInput > div > div > input {
        direction: rtl;
        text-align: right;
        font-family: "Tajawal", sans-serif;
    }
    
    .stTextArea > div > div > textarea {
        direction: rtl;
        text-align: right;
        font-family: "Tajawal", sans-serif;
        border: 2px solid #1D5038;
        border-radius: 10px;
        background-color: rgba(217, 217, 217, 0.56);
        width: 70%;
        height: 10%;
        margin: 0 auto;
    }
    
    .st-b1 {
        border: none;
        background-color: transparent;
    }

    .st-bs {
        background: white;
    }

    .st-emotion-cache-8atqhb {
        display: flex;
    }
    
    .stButton > button {
        background-color: #1D5038;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: bold;
        font-family: "Tajawal", sans-serif;
        width: 30%;
        padding: 12px;
        margin: 0 auto;
    }
    
    .stButton > button:hover {
        background-color: #005527;
        color: white;
    }
    
    .loading-spinner {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
    }
    
    .spinner {
        width: 48px;
        height: 48px;
        border: 5px solid #006633;
        border-bottom-color: transparent;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .stChatMessage {
        direction: rtl;
    }
    
    div[data-testid="stChatMessageContent"] {
        direction: rtl;
        text-align: right;
    }
    
    .stAppHeader.st-emotion-cache-12fmjuu.e4hpqof0 {
        background: #EAEAEA !important;
        position: relative;
    }

    .stAppHeader.st-emotion-cache-12fmjuu.e4hpqof0::before {
        content: "الـجــمهورية الجــزائرية الديمقراطية الشعبية \\A رئاسة الجمهورية";
        white-space: pre;
        color: #1D5038;
        font-size: 16px;
        text-align: center;
        width: 100%;
        position: absolute;
        top: 50%;
        left: 0;
        transform: translateY(-50%);
        font-weight: 700;
        line-height: 1.4;
        margin-top: 5px;
        margin-bottom: 2px;
        pointer-events: none;
    }
    
    .st-emotion-cache-t1wise {
        padding: 2rem 0 0;
    }

    .input-container {
        position: relative;
        width: 100%;
    }

    .inside-button {
        position: absolute;
        right: 8px;
        top: 6px;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background-color: #1D5038;
        color: white;
        border: none;
        padding: 4px 8px;
        font-size: 14px;
        border-radius: 4px;
        z-index: 1;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .st-emotion-cache-ocqkz7 {
        position: fixed;
        bottom: 10px;
        padding-top: 6px;
        width: 100%;
        background: white;
    }

    .hidden-button {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

def image_to_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Convert images to base64
img1_base64 = image_to_base64("./images/dz_image.png")
img2_base64 = image_to_base64("./images/law_image.png")

# Header
st.markdown(f"""
<div class="header-container">
    <div class="header-content" >
        <img src="data:image/png;base64,{img1_base64}" alt="alg" style="width: 60px; height: 60px; border-radius: 50%;" />
        <div class="title-container">
            <div class="sub-title">الأمانة العامة للحكومة</div>
        </div>
        <img src="data:image/png;base64,{img2_base64}" alt="jus" style="width: 60px; height: 60px; border-radius: 50%;"" />
    </div>
    <div class="language-selector">العربية</div>
</div>
""", unsafe_allow_html=True)


# Initialize session state variables for existing chat functionality
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "first_message" not in st.session_state:
    st.session_state.first_message = True

# Initialize session state variables for dynamic UI
if 'is_loading' not in st.session_state:
    st.session_state.is_loading = False
if 'query_submitted' not in st.session_state:
    st.session_state.query_submitted = False
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

def handle_submit():
    """Handle the submit button click"""
    # Get the current input value using the dynamic key
    input_key = f"user_input_{st.session_state.input_key}"
    query = st.session_state.get(input_key, "")
    if query.strip():  # Only proceed if query is not empty
        st.session_state.last_query = query
        st.session_state.is_loading = True
        st.session_state.query_submitted = True
        st.session_state.processing = True
        st.session_state.first_message = False
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": query.strip()})
        # Increment key to reset the input
        st.session_state.input_key += 1

def reset_loading():
    """Reset loading state after delay"""
    st.session_state.is_loading = False
    st.session_state.processing = False

# Chat heading (only show if no messages)
if not st.session_state.messages:
    st.markdown('<div class="chat-heading">مــــا الذي تريد معرفته في القانون؟</div>', unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-message">{message["content"]}</div>', unsafe_allow_html=True)

if st.session_state.is_loading:
    # Loading state: show spinner
    with st.container():
        st.markdown('<div class="loading-spinner"><div class="spinner"></div></div>', unsafe_allow_html=True)
        time.sleep(2)
    
    # Generate bot response after loading
    if st.session_state.last_query:
        rag_response, html_links, original_lang = advanced_rag_query(st.session_state.last_query)
        direction = "rtl" if original_lang else "ltr"
        alignment = "right" if original_lang else "left"
        if rag_response is None:
            bot_response = '''
                <div class="response-title">
                    <span class="title-icon">🤖</span> الإجابة :
                </div>
                <div class="message-content">
                    عذراً، لا يمكنني الإجابة على هذا السؤال حالياً. يرجى التأكد من صياغة السؤال بشكل صحيح أو طرح سؤال آخر متعلق بالقوانين الجزائرية.<br><br>
                    • تأكد من كتابة السؤال بشكل واضح<br>
                    • حاول استخدام مصطلحات قانونية دقيقة<br>
                    • يمكنك طرح سؤال حول قوانين الأسرة، العمل، العقارات، أو القانون المدني
                </div>
                <div class="response-title">
                    <span class="title-icon">📂</span> مصدر المعلومات:
                </div>
                <div class="info-source">
                    المنظومة القانونية الجزائرية - دليل المستخدم
                </div>
            '''
        else:
            bot_response = f'''
                <div class="response-title" style="direction: rtl; text-align: right;">
                    <span class="title-icon">🤖</span> الإجابة :
                </div>
                <div class="message-content" style="direction: {direction}; text-align: {alignment};">
                    {rag_response}
                </div>
                <div class="response-title" style="direction: rtl; text-align: right;">
                    <span class="title-icon">📂</span> مصدر المعلومات:
                </div>
                <div class="info-source">
                    {html_links}
                </div>
            '''
        
        # Add bot response to messages
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
    
    # After loading, reset state and rerun
    reset_loading()
    st.rerun()

elif st.session_state.query_submitted:
    # After first submission: input and button at bottom (button on left, input on right)
    col1, col2 = st.columns([2, 10])  # Button smaller, input larger
    
    with col1:
        st.write("")  # Add spacing to align button with input
        send_button = st.button("إرسال", key=f"submit_{st.session_state.input_key}")
    
    with col2:
        user_input = st.text_area(
            "اكتب سؤالك هنا...", 
            key=f"user_input_{st.session_state.input_key}",
            label_visibility="collapsed",
            height=80,
            placeholder="اكتب سؤالك هنا..."
        )
    st.markdown(
        """
        <div style='text-align: center; font-size: 16px; color: #666; position: fixed; bottom: 0; left: 30%; transform: translateX(-20%); background: white;'>
             .سيتم الرد على سؤالك بناءً على الوثائق القانونية المتوفرة فقط. يرجى التحقق من المعلومات المتحصل عليها
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Handle new submission
    if send_button and user_input and user_input.strip():
        st.session_state.last_query = user_input.strip()
        st.session_state.is_loading = True
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        st.session_state.input_key += 1
        st.rerun()

else:
    # Initial state: input above button
    user_input = st.text_area(
        "اكتب سؤالك هنا...",
        key=f"user_input_{st.session_state.input_key}",
        height=100,
        label_visibility="collapsed",
        placeholder="اكتب سؤالك هنا..."
    )
    
    send_button = st.button(
        "إرسال", 
        key=f"submit_{st.session_state.input_key}",
        on_click=handle_submit
    )
