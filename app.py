"""
🌍 Avrupa Tur Rehberi Chatbot
AI-powered RAG chatbot for European city travel information
"""

import os
from dotenv import load_dotenv
import gradio as gr
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import wikipedia

# .env dosyasından API key'i yükle
load_dotenv()

# API KEY kontrolü
if "GROQ_API_KEY" not in os.environ:
    print("❌ GROQ_API_KEY bulunamadı!")
    print("📝 .env dosyası oluşturup API key'inizi ekleyin")
    raise Exception("GROQ_API_KEY gerekli!")

print("🔧 Sistem hazırlanıyor...\n")

# Türkçe Wikipedia
wikipedia.set_lang("tr")

# === AI MODELLERİ ===
print("🤖 AI modelleri yükleniyor...")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7
)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
print("✓ Modeller hazır\n")

# === VERİ TOPLAMA ===
print("📥 Wikipedia'dan Avrupa şehirleri bilgisi çekiliyor...\n")

cities = [
    "Londra", "Paris", "Brüksel", "Amsterdam", "Lüksemburg",
    "Oslo", "Stockholm", "Kopenhag", "Helsinki", "Reykjavik",
    "Lizbon", "Madrid", "Roma", "Atina", "Valletta",
    "Viyana", "Berlin", "Bern", "Prag", "Bratislava", "Budapeşte",
    "Barselona", "Milan", "Valencia", "Munih"
]

documents = []
for city in cities:
    try:
        print(f"  • {city}...", end=" ")
        summary = wikipedia.summary(city, sentences=5)
        page = wikipedia.page(city)
        
        content = f"""
ŞEHİR: {city}
ÖZET: {summary}
DETAYLAR: {page.content[:1500]}
"""
        documents.append(Document(
            page_content=content, 
            metadata={'city': city}
        ))
        print("✓")
    except:
        print("✗")
        continue

print(f"\n✓ {len(documents)} şehir yüklendi\n")

# === VEKTÖR VERİTABANI ===
print("🔮 Vektör veritabanı oluşturuluyor...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
texts = text_splitter.split_documents(documents)
vector_store = FAISS.from_documents(texts, embeddings)
print(f"✓ Hazır ({len(texts)} parça)\n")

# === SORU-CEVAP ZİNCİRİ ===
prompt_template = """
Sen bir Avrupa seyahat danışmanısın. Verilen bilgileri kullanarak soruya samimi ve detaylı cevap ver.

Bağlam: {context}
Soru: {question}
Cevap:
"""
prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt)

# === CHATBOT FONKSİYONU ===
def chatbot_response(user_message, history):
    try:
        docs = vector_store.similarity_search(user_message, k=3)
        response = chain.invoke({
            "input_documents": docs,
            "question": user_message
        })
        return response["output_text"]
    except Exception as e:
        return f"❌ Hata: {str(e)}"

# === GRADIO ARAYÜZÜ ===
print("🚀 WEB ARAYÜZÜ BAŞLATILIYOR...\n")

demo = gr.ChatInterface(
    fn=chatbot_response,
    title="🌍 Avrupa Tur Rehberi Chatbot",
    description="Merhaba! Ben Avrupa şehirleri hakkında bilgi veren bir chatbot'um.",
    examples=[
        "Roma'da ne yapmalıyım?",
        "Paris'te gezilecek yerler neler?",
        "Barselona'da hangi yemekleri denemeli?"
    ]
)

if __name__ == "__main__":
    demo.launch(share=True, debug=False)
