from io import BytesIO
import streamlit as st
import base64
import time

# Configure page
st.set_page_config(
    page_title="روبوت محادثة قانوني مدعوم بالذكاء الاصطناعي",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
        direction: rtl;
        text-align: right;
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
        direction: rtl;
        text-align: right;
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
        direction: rtl;
        text-align: right;
    }
    
    .info-source a {
        color: #1D5038;
        text-decoration: none;
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
    
    .stButton > button {
        background-color: #1D5038;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: bold;
        font-family: "Tajawal", sans-serif;
        width: 100%;
        padding: 12px;
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
        padding: 2rem 0 10rem;
    }
</style>
""", unsafe_allow_html=True)

def image_to_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Convert images to base64
img1_base64 = image_to_base64("image_5.png")
img2_base64 = image_to_base64("image_4.png")

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

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "first_message" not in st.session_state:
    st.session_state.first_message = True

# Sample responses dictionary
responses = {
    'متى تم انهاء مهام وزير التجارة الخارجية وترقية الصادرات محمد بوخاري؟': {
        'answer': '''تم انهاء مهام وزير التجارة الخارجية وترقية الصادرات محمد بوخاري, بناءً على الدستور، وخاصة المواد 91-7 منه، بمقتضى المرسوم الرئاسي رقم 24-374 المؤرخ في 16 جمادى الأولى عام 1446 هـ، الموافق 18 نوفمبر سنة 2024، والمتضمن تعيين أعضاء الحكومة، المعدل، أصدر رئيس الجمهورية، وزير الدفاع الوطني، مرسوما رئاسيا رقم 25-109 المؤرخ في 15 شوال 1446 الموافق ل 14 أفريل 2025 حيث تنص المادة الأولى على انهاء مهام السيد محمد بوخاري وزير التجارة الخارجية وترقية الصادرات. وتوضح المادة الثانية أن هذا المرسوم سيُنشر في الجريدة الرسمية للجمهورية الجزائرية الديمقراطية الشعبية.''',
        'source': 'الجريدة الرسمية رقم 22 عام 2025',
        'link': 'https://www.joradp.dz/FTP/jo-arabe/2025/A2025022.pdf'
    },
    'كيف يتم تنظيم وضعية المواطنين بعد انهاء خدمتهم العسكرية؟': {
        'answer': '''يتضمن القانون رقم 20-22 المؤرخ في 3 محرم عام 1444 هـ، الموافق لأول أغسطس 2022، و الذي يتعلق بتنظيم الاحتياط العسكري في الجزائر و يهدف الى تحديد الإطار القانوني الذي يُنظم علاقة الدولة بالمواطنين الذين يُستدعون للخدمة في إطار الاحتياط بعد انتهاء خدمتهم العسكرية أو الوطنية, و الذي جاء لتحديد الحقوق والواجبات المرتبطة بهذه الوضعية بشكل دقيق، ما يلي:

• تعريف الاحتياط العسكري: يتمثل في مجموعة المواطنين الذين أنهوا خدمتهم الوطنية أو العسكرية ويمكن استدعاؤهم عند الحاجة لتعزيز القوات المسلحة الوطنية.

• شروط الاستدعاء: يُمكن استدعاء الاحتياطيين في حالات التمرينات، المناورات، أو في حالات استثنائية مثل الكوارث أو التهديدات الأمنية.

• الواجبات: تشمل الالتزام بالحضور في الوقت المحدد، التحلي بالانضباط العسكري، واحترام السرية المهنية.

• الحقوق: يضمن القانون للمنتسبين للاحتياط الحق في التعويض المالي خلال فترة الاستدعاء، والاحتفاظ بمنصبهم الوظيفي، بالإضافة إلى الاستفادة من التغطية الاجتماعية والصحية.

• العقوبات: ينص القانون على تطبيق إجراءات تأديبية أو قانونية في حال عدم الامتثال للاستدعاء أو مخالفة التعليمات العسكرية.''',
        'source': 'الجريدة الرسمية رقم 52 عام 2022. لمزيد من المعلومات أنقر هنا',
        'link': 'https://www.joradp.dz/FTP/jo-arabe/2022/A2022052.pdf'
    }
}

# Chat heading (only show if no messages)
if not st.session_state.messages:
    st.markdown('<div class="chat-heading">مــــا الذي تريد معرفته في القانون؟</div>', unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-message">{message["content"]}</div>', unsafe_allow_html=True)

# Chat input
user_input = st.text_area(
    "اكتب سؤالك هنا...",
    key="user_input",
    height=100,
    label_visibility="collapsed",
    placeholder="اكتب سؤالك هنا..."
)

# Initialize session state flags
if "processing" not in st.session_state:
    st.session_state.processing = False
if "first_message" not in st.session_state:
    st.session_state.first_message = True
if "messages" not in st.session_state:
    st.session_state.messages = []

# Send button
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    if not st.session_state.processing:
        send_button = st.button("إرسال" if st.session_state.first_message else "↑", use_container_width=True)
    else:
        send_button = False  # Block sending while processing

# Handle message sending
if send_button and user_input.strip():
    st.session_state.processing = True  # Set flag to hide button next rerun

    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input.strip()})
    
    with st.container():
        st.markdown('<div class="loading-spinner"><div class="spinner"></div></div>', unsafe_allow_html=True)
        time.sleep(2)

    # Done processing
    st.session_state.processing = False
    st.session_state.first_message = False
    
    # Generate response
    if user_input.strip() in responses:
        response_data = responses[user_input.strip()]
        bot_response = f'''
        <div class="response-title">
            <span class="title-icon">🤖</span> الإجابة :
        </div>
        <div class="message-content">
            {response_data['answer']}
        </div>
        <div class="response-title">
            <span class="title-icon">📂</span> مصدر المعلومات:
        </div>
        <div class="info-source">
            {response_data['source']} <a href="{response_data['link']}" target="_blank">{response_data['link']}</a>
        </div>
        '''
    else:
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
    
    # Add bot response
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    
    # Update first message flag
    st.session_state.first_message = False
    
    # Clear input and rerun
    st.rerun()
