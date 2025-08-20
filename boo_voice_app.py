import streamlit as st
import requests
import mimetypes
import os

st.title("🎤 Boo Voice Logistics App")

DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]

url = "https://api.deepgram.com/v1/listen"

def transcribe_audio(file_path):
    # Đoán loại file audio (wav, mp3, m4a)
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "audio/mpeg"  # fallback cho mp3

    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": mime_type
    }

    params = {
        "model": "nova-2",
        "language": "vi"
    }

    with open(file_path, "rb") as f:
        response = requests.post(url, headers=headers, params=params, data=f)

    return response.json()

uploaded_file = st.file_uploader("📂 Upload file ghi âm (.mp3, .wav, .m4a)", type=["mp3", "wav", "m4a"])

if uploaded_file is not None:
    # Lưu file tạm
    file_path = os.path.join("/tmp", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.audio(file_path)

    st.write("⏳ Đang nhận diện giọng nói...")
    result = transcribe_audio(file_path)

    if "results" in result:
        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
        st.success(f"📝 Nội dung: {transcript}")
    else:
        st.error("⚠️ Lỗi khi nhận diện: " + str(result))
Fix Deepgram audio upload & report generator
