import os
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
import gradio as gr

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY)

# ── TOOL 1: Fashion Trends ──────────────────────────────────────
def get_fashion_trends(topic: str) -> str:
    """Fetch latest fashion news from free RSS feeds."""
    feeds = [
        "https://www.vogue.com/feed/rss",
        "https://wwd.com/feed/",
    ]
    headlines = []
    for feed_url in feeds:
        try:
            response = requests.get(feed_url, timeout=5)
            root = ET.fromstring(response.content)
            for item in root.findall(".//item")[:5]:
                title = item.find("title")
                if title is not None:
                    headlines.append(f"• {title.text}")
        except:
            continue

    if not headlines:
        return "Could not fetch fashion news right now."

    return f"Latest fashion & style headlines:\n" + "\n".join(headlines[:8])

# ── TOOL 2: VS Brand Knowledge RAG ─────────────────────────────
loader = DirectoryLoader(
    "./docs",
    glob="**/*.md",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"}
)
documents = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=GEMINI_API_KEY)
vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings)
print("✅ VS Marketing Bot ready!")

def answer_brand_question(question: str) -> str:
    """Answer questions about VS brand using RAG."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(question)
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = ChatPromptTemplate.from_template("""
You are a Victoria's Secret marketing expert. Use the context below to answer 
the question in VS's glamorous, confident brand voice.

Context: {context}
Question: {question}
Answer:""")

    chain = prompt | llm
    result = chain.invoke({"context": context, "question": question})
    return result.content

# ── TOOL 3: Caption Writer ──────────────────────────────────────
def write_vs_caption(product: str) -> str:
    """Write an Instagram caption in Victoria's Secret brand voice."""
    prompt = ChatPromptTemplate.from_template("""
You are a Victoria's Secret social media copywriter. 
Write 3 Instagram caption options for the following product or campaign.
Keep each caption short, punchy, glamorous and empowering.
Use sensory words. End with a feeling or call to action.
Include relevant hashtags.

Product/Campaign: {product}

Captions:""")
    chain = prompt | llm
    result = chain.invoke({"product": product})
    return result.content

# ── CLASSIFIER ──────────────────────────────────────────────────
classifier_prompt = ChatPromptTemplate.from_template("""
You are a Victoria's Secret marketing assistant router.
Classify the following message into exactly ONE category.
Respond with ONLY the category name, nothing else.

Categories:
- TRENDS: User wants fashion news, trends, or what's popular
- BRAND: User asks about VS brand voice, campaigns, or marketing strategy
- CAPTION: User wants captions, copy, taglines, or social media content written

Message: {message}

Category:""")

classifier_chain = classifier_prompt | llm

def classify_message(message: str) -> str:
    result = classifier_chain.invoke({"message": message})
    category = result.content.strip().upper()
    for valid in ["TRENDS", "BRAND", "CAPTION"]:
        if valid in category:
            return valid
    return "BRAND"

def handle_message(message: str) -> str:
    category = classify_message(message)
    print(f"Classified as: {category}")
    if category == "TRENDS":
        return get_fashion_trends(message)
    elif category == "BRAND":
        return answer_brand_question(message)
    elif category == "CAPTION":
        return write_vs_caption(message)

# ── GRADIO UI ───────────────────────────────────────────────────
def chat_fn(message, history):
    return handle_message(message)

custom_css = """
.gradio-container {
    background: linear-gradient(135deg, #ffb3cb, #ffc6ef, #ffb5ee) !important;
    font-family: 'Playfair Display', Georgia, serif !important;
}
.chat-bubble-bot {
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 1px solid #ffb3cb !important;
}
.chat-bubble-user {
    background-color: #ffb3cb !important;
    color: #000000 !important;
}
button.primary {
    background-color: #ffb3cb !important;
    color: #000000 !important;
    border-radius: 25px !important;
    border: none !important;
}
footer {display: none !important;}
"""

custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap');

.gradio-container {
    background: linear-gradient(160deg, #ffffff, #fff0f5, #ffe4f0) !important;
    font-family: 'Playfair Display', Georgia, serif !important;
}
.dark, [data-theme="dark"] {
    --background-fill-primary: #ffffff !important;
    --background-fill-secondary: #fff0f5 !important;
    --body-text-color: #000000 !important;
    --color-accent: #c9a84c !important;
}
.message, .message-bubble-border, .bot, .user, .message-wrap, .wrap {
    background-color: #ffffff !important;
    color: #000000 !important;
    border-color: #c9a84c !important;
}
.chatbot {
    background-color: #fff0f5 !important;
    color: #000000 !important;
}
textarea, input {
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 2px solid #c9a84c !important;
    border-radius: 25px !important;
}
button {
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 2px solid #c9a84c !important;
    border-radius: 25px !important;
}
button:hover {
    background-color: #c9a84c !important;
    color: #ffffff !important;
}
footer {display: none !important;}
"""

with gr.Blocks(css=custom_css, theme=gr.themes.Soft(), title="💗 VS Marketing Assistant") as demo:

    gr.Markdown("""
    # ✨ Victoria's Secret Marketing Assistant
    *Your AI-powered marketing companion — glamorous, bold, and always on-brand.*
    
    ---
    """)

    gr.ChatInterface(
        fn=chat_fn,
        examples=[
            "What's trending in fashion right now?",
            "What tone does Victoria's Secret use?",
            "Write me a caption for a new bra launch",
            "Give me campaign ideas for Valentine's Day",
            "Write 3 Instagram captions for our PINK collection"
        ],
    )

    gr.Markdown("""
    ---
    *Powered by LangChain + Gemini AI | Built for Victoria's Secret Marketing*
    """)



demo.launch(share=True)