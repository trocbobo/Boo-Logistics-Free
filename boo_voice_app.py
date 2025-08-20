import streamlit as st
import pandas as pd
import os
from datetime import datetime
from deepgram import Deepgram
import asyncio
import aiofiles

# API Key Deepgram
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Hàm nhận diện giọng nói bằng Deepgram
async def transcribe_audio(file_path):
    dg_client = Deepgram(DEEPGRAM_API_KEY)
    mimetype = "audio/m4a" if file_path.endswith(".m4a") else "audio/wav"
    async with aiofiles.open(file_path, "rb") as audio:
        source = {"buffer": await audio.read(), "mimetype": mimetype}
        response = await dg_client.transcription.prerecorded(source, {"smart_format": True, "language": "vi"})
        return response["results"]["channels"][0]["alternatives"][0]["transcript"]

# Hàm tạo báo cáo chi phí
def generate_cost_report(data_file, month):
    df = pd.read_excel(data_file)

    # Lọc dữ liệu theo tháng
    df["Tháng"] = pd.to_datetime(df["Ngày"]).dt.month
    report = df[df["Tháng"] == month]

    # Xuất ra Excel
    output_file = f"bao_cao_T{month}.xlsx"
    report.to_excel(output_file, index=False)
    return output_file

# Giao diện Streamlit
st.title("📊 Trợ lý Boo - Báo cáo Logistics bằng giọng nói")

uploaded_file = st.file_uploader("Tải file dữ liệu (Excel)", type=["xlsx"])
uploaded_audio = st.file_uploader("🎤 Gửi file ghi âm lệnh", type=["mp3", "wav", "m4a"])

if uploaded_audio is not None:
    file_path = os.path.join("/tmp", uploaded_audio.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_audio.getbuffer())
    
    st.audio(file_path)

    st.write("⏳ Đang nhận diện giọng nói...")
    transcript = asyncio.run(transcribe_audio(file_path))
    st.success(f"📌 Nội dung: {transcript}")

    if "báo cáo doanh thu tháng sáu" in transcript.lower():
        if uploaded_file is not None:
            output = generate_cost_report(uploaded_file, 6)
            st.success("✅ Báo cáo đã tạo xong!")
            with open(output, "rb") as f:
                st.download_button("⬇️ Tải báo cáo Excel", f, file_name=output)
a
