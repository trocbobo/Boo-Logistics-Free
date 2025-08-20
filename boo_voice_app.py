import streamlit as st
import pandas as pd
import requests
import mimetypes
import os

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
url = "https://api.deepgram.com/v1/listen"

# --- Nhận diện giọng nói ---
def transcribe_audio(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "audio/mpeg"

    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}", "Content-Type": mime_type}
    params = {"model": "nova-2", "language": "vi"}

    with open(file_path, "rb") as f:
        response = requests.post(url, headers=headers, params=params, data=f)

    return response.json()

# --- Báo cáo doanh thu (bản đơn giản) ---
def generate_revenue_simple(data_file, month):
    df = pd.read_excel(data_file)
    df["Tháng"] = pd.to_datetime(df["Ngày"], errors="coerce").dt.month
    report = df[df["Tháng"] == month].groupby("Khách hàng")["Tổng VND"].sum().reset_index()
    out = f"Bao_cao_doanh_thu_T{month}_simple.xlsx"
    report.to_excel(out, index=False)
    return out

# --- Báo cáo doanh thu (bản nâng cấp theo mẫu anh gửi) ---
def generate_revenue_detailed(data_file, month):
    df = pd.read_excel(data_file)
    df["Tháng"] = pd.to_datetime(df["Ngày"], errors="coerce").dt.month
    df_month = df[df["Tháng"] == month]

    # Gom theo khách hàng + loại cont
    report = df_month.groupby(["Khách hàng", "Loại cont"]).agg({
        "Số lượng": "sum",
        "Tổng VND": "sum",
        "TỔNG (VC+PS)": "sum"
    }).reset_index()

    # Xuất ra Excel với nhiều sheet
    out = f"Bao_cao_doanh_thu_T{month}_detailed.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        report.to_excel(writer, sheet_name="Chi tiết theo cont", index=False)
        df_month.groupby("Khách hàng")["Tổng VND"].sum().reset_index().to_excel(writer, sheet_name="Tổng hợp KH", index=False)

    return out

# --- Xử lý transcript ---
def handle_command(transcript, data_file):
    transcript = transcript.lower()
    if "doanh thu" in transcript and "tháng sáu" in transcript:
        simple = generate_revenue_simple(data_file, 6)
        detailed = generate_revenue_detailed(data_file, 6)
        return [simple, detailed]
    return []

# --- Giao diện Streamlit ---
st.title("🎤 Boo Voice Logistics Assistant")

uploaded_audio = st.file_uploader("Upload file ghi âm (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])
uploaded_excel = st.file_uploader("Upload file Excel dữ liệu", type=["xlsx"])

if uploaded_audio and uploaded_excel:
    file_path = os.path.join("/tmp", uploaded_audio.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_audio.getbuffer())
    st.audio(file_path)

    st.write("⏳ Đang nhận diện giọng nói...")
    result = transcribe_audio(file_path)

    if "results" in result:
        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
        st.success(f"📝 Nội dung: {transcript}")

        reports = handle_command(transcript, uploaded_excel)
        for r in reports:
            with open(r, "rb") as f:
                st.download_button(f"⬇️ Tải {r}", f, file_name=r)
    else:
        st.error("⚠️ Không nhận diện được giọng nói.")
