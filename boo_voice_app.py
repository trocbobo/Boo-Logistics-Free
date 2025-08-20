import os
import streamlit as st
import pandas as pd
import re
from deepgram import Deepgram

# ===================== CONFIG =====================
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY") or st.secrets["DEEPGRAM_API_KEY"]
dg_client = Deepgram(DEEPGRAM_API_KEY)

st.set_page_config(page_title="Boo Voice Logistics Assistant", page_icon="🎤", layout="centered")
st.title("🎤 Boo Voice Logistics Assistant")

# ===================== UTILS =====================
def normalize_command(text: str) -> str:
    """Chuẩn hóa câu lệnh tiếng Việt"""
    text = text.lower()
    text = re.sub(r"tháng\s*(\d+)", r"T\1", text)   # "tháng 6" => "T6"
    mapping = {
        "tháng một": "T1", "tháng hai": "T2", "tháng ba": "T3",
        "tháng tư": "T4", "tháng năm": "T5", "tháng sáu": "T6",
        "tháng bảy": "T7", "tháng tám": "T8", "tháng chín": "T9",
        "tháng mười": "T10", "tháng mười một": "T11", "tháng mười hai": "T12"
    }
    for k,v in mapping.items():
        text = text.replace(k, v)
    return text

def extract_month(command):
    """Tìm tháng trong câu lệnh"""
    match = re.search(r"T(\d+)", command)
    if match:
        return int(match.group(1))
    return None

def transcribe_audio(file_path):
    """Nhận diện giọng nói bằng Deepgram"""
    with open(file_path, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/wav"}
        response = dg_client.transcription.sync_prerecorded(
            source,
            {"punctuate": True, "language": "vi"}
        )
    return response["results"]["channels"][0]["alternatives"][0]["transcript"]

# ===================== REPORTS =====================
def generate_revenue_simple(data_file, month):
    df = pd.read_excel(data_file, engine="openpyxl")
    if "Ngay" in df.columns:
        df["Thang"] = pd.to_datetime(df["Ngay"]).dt.month
    else:
        st.warning("⚠️ File Excel chưa có cột 'Ngay'")
        return pd.DataFrame()
    result = df[df["Thang"] == month].groupby("KhachHang")["DoanhThu"].sum().reset_index()
    return result

def generate_cost_report(data_file, month):
    df = pd.read_excel(data_file, engine="openpyxl")
    if "Ngay" in df.columns:
        df["Thang"] = pd.to_datetime(df["Ngay"]).dt.month
    else:
        return pd.DataFrame()
    result = df[df["Thang"] == month].groupby("Vendor")["ChiPhi"].sum().reset_index()
    return result

def generate_container_report(data_file, cont_size):
    df = pd.read_excel(data_file, engine="openpyxl")
    col = f"SL_{cont_size}"
    if col not in df.columns:
        st.warning(f"⚠️ File Excel chưa có cột {col}")
        return pd.DataFrame()
    result = df.groupby("KhachHang")[col].sum().reset_index()
    return result

def generate_lcl_report(data_file):
    df = pd.read_excel(data_file, engine="openpyxl")
    if "SL_LCL" not in df.columns:
        st.warning("⚠️ File Excel chưa có cột SL_LCL")
        return pd.DataFrame()
    result = df.groupby("KhachHang")["SL_LCL"].sum().reset_index()
    return result

def generate_summary_report(data_file):
    df = pd.read_excel(data_file, engine="openpyxl")
    if not {"DoanhThu","ChiPhi"}.issubset(df.columns):
        st.warning("⚠️ File Excel chưa có cột DoanhThu hoặc ChiPhi")
        return pd.DataFrame()
    result = df.groupby("KhachHang")[["DoanhThu", "ChiPhi"]].sum().reset_index()
    result["LoiNhuan"] = result["DoanhThu"] - result["ChiPhi"]
    return result

# ===================== COMMAND HANDLER =====================
def handle_command(command, data_file):
    if "doanh thu" in command:
        month = extract_month(command)
        if month:
            return generate_revenue_simple(data_file, month)
    elif "chi phí" in command:
        month = extract_month(command)
        if month:
            return generate_cost_report(data_file, month)
    elif "container" in command:
        if "20" in command:
            return generate_container_report(data_file, 20)
        elif "40" in command:
            return generate_container_report(data_file, 40)
    elif "lcl" in command:
        return generate_lcl_report(data_file)
    elif "tổng hợp" in command or "hiệu suất" in command:
        return generate_summary_report(data_file)
    return pd.DataFrame({"Thông báo": ["⚠️ Chưa hiểu lệnh, vui lòng thử lại."]})

# ===================== UI =====================
uploaded_audio = st.file_uploader("🎤 Upload file ghi âm (.wav)", type=["wav"])
uploaded_excel = st.file_uploader("📊 Upload file Excel dữ liệu", type=["xlsx"])

if uploaded_audio and uploaded_excel:
    # Lưu file audio tạm
    audio_path = os.path.join("/tmp", uploaded_audio.name)
    with open(audio_path, "wb") as f:
        f.write(uploaded_audio.getbuffer())

    # Bắt buộc WAV
    if not audio_path.endswith(".wav"):
        st.error("⚠️ Chỉ hỗ trợ file WAV. Vui lòng convert file ghi âm trước khi upload.")
        st.stop()

    # Phát lại audio
    st.audio(audio_path)

    # Nhận diện giọng nói
    st.write("⏳ Đang nhận diện giọng nói...")
    try:
        transcript = transcribe_audio(audio_path)
        st.success(f"📝 Nội dung: {transcript}")

        # Chuẩn hóa câu lệnh
        command = normalize_command(transcript)

        # Xử lý lệnh
        reports = handle_command(command, uploaded_excel)

        st.subheader("📊 Kết quả báo cáo:")
        st.dataframe(reports)

        # Xuất file Excel
        output_path = "/tmp/bao_cao.xlsx"
        reports.to_excel(output_path, index=False)
        with open(output_path, "rb") as f:
            st.download_button("⬇️ Tải báo cáo Excel", f, file_name="bao_cao.xlsx")

    except Exception as e:
        st.error(f"Lỗi Deepgram: {e}")
