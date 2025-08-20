import streamlit as st
import requests
import tempfile
from gtts import gTTS
import os

st.set_page_config(page_title="Boo Logistics Free", page_icon="🎤", layout="wide")

st.title("🎤 Trợ lý Boo Logistics (Free version)")
st.write("👉 Upload file giọng nói (.wav / .mp3 / .m4a) để Boo nhận diện và trả lời")

# 🔑 API Keys (điền vào Streamlit Secrets)
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
HUGGINGFACE_API_KEY = st.secrets["HUGGINGFACE_API_KEY"]

# 🎤 Upload file audio
uploaded_audio = st.file_uploader("🎙️ Upload file giọng nói", type=["wav", "mp3", "m4a"])

query = ""
if uploaded_audio:
    with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_audio.name.split(".")[-1]) as tmpfile:
        tmpfile.write(uploaded_audio.read())
        tmp_path = tmpfile.name

    # 🎤 Gọi Deepgram Speech-to-Text
    url = "https://api.deepgram.com/v1/listen?language=vi"
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
    with open(tmp_path, "rb") as audio_file:
        resp = requests.post(url, headers=headers, data=audio_file)
    try:
        query = resp.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
        st.success(f"Anh nói: {query}")
    except:
        st.error("❌ Không nhận diện được giọng nói từ file audio.")
        st.json(resp.json())

# 🧠 Xử lý yêu cầu bằng HuggingFace model (free)
if query:
    st.write("### 📊 Boo đang trả lời...")

    hf_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": f"Bạn là Trợ lý Boo chuyên logistics. Hãy trả lời ngắn gọn: {query}"}

    response = requests.post(hf_url, headers=headers, json=payload)
    try:
        answer = response.json()[0]["generated_text"]
    except:
        answer = "❌ Lỗi khi gọi HuggingFace API"
        st.json(response.json())

    st.write(answer)

    # 🎧 Xuất ra file mp3 để nghe
    tts = gTTS(answer, lang="vi")
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmpfile.name)
    st.audio(tmpfile.name, format="audio/mp3")

    # Hiển thị text Boo nói
    st.success(f"🟢 Boo: {answer}")