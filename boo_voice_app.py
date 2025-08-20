import streamlit as st
import pandas as pd
import requests
import mimetypes
import osimport os
import streamlit as st
import pandas as pd
import requests

# =====================
# Cấu hình mặc định
# =====================
DEFAULT_DATA_FILE = "data/OTM_MASTER_DATA.xlsx"
DEEPGRAM_API_KEY = st.secrets.get("DEEPGRAM_API_KEY", "")

# =====================
# Hàm gọi Deepgram API
# =====================
def transcribe_audio(file_path):
    url = "https://api.deepgram.com/v1/listen"
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}

    with open(file_path, "rb") as f:
        response = requests.post(
            url, headers=headers, files={"file": f}, data={"model": "nova-2", "language": "vi"}
        )

    if response.status_code == 200:
        return response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
    else:
        st.error(f"Lỗi Deepgram: {response.text}")
        return ""

# =====================
# Hàm xử lý dữ liệu Excel
# =====================
def generate_revenue_simple(data_file, month):
    df = pd.read_excel(data_file)

    if "Tháng" not in df.columns or "Doanh thu" not in df.columns:
        return pd.DataFrame({"Lỗi": ["Thiếu cột 'Tháng' hoặc 'Doanh thu' trong file dữ liệu"]})

    df_month = df[df["Tháng"] == month]
    summary = df_month.groupby("Khách hàng")["Doanh thu"].sum().reset_index()
    return summary

# =====================
# Xử lý lệnh từ giọng nói
# =====================
def handle_command(command, data_file):
    command = command.lower()
    if "doanh thu" in command and "tháng sáu" in command:
        return generate_revenue_simple(data_file, 6)
    elif "doanh thu" in command and "tháng bảy" in command:
        return generate_revenue_simple(data_file, 7)
    else:
        return pd.DataFrame({"Thông báo": ["Chưa hiểu lệnh, vui lòng thử lại."]})

# =====================
# Hàm lấy file Excel (upload hoặc mặc định)
# =====================
def get_data_file(uploaded_file):
    if uploaded_file is not None:
        file_path = os.path.join("/tmp", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    else:
        return DEFAULT_DATA_FILE

# =====================
# Giao diện Streamlit
# =====================
st.set_page_config(page_title="Boo Voice Logistics Assistant", layout="centered")

st.title("🎤 Boo Voice Logistics Assistant")

uploaded_audio = st.file_uploader("Upload file ghi âm (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])
uploaded_excel = st.file_uploader("Upload file Excel dữ liệu", type=["xlsx"])

if uploaded_audio:
    # Lưu file ghi âm
    audio_path = os.path.join("/tmp", uploaded_audio.name)
    with open(audio_path, "wb") as f:
        f.write(uploaded_audio.getbuffer())

    st.audio(audio_path)

    st.write("⏳ Đang nhận diện giọng nói...")
    transcript = transcribe_audio(audio_path)
    st.success(f"📝 Nội dung: {transcript}")

    # Lấy file Excel (upload hoặc mặc định)
    data_file = get_data_file(uploaded_excel)

    # Xử lý lệnh và tạo báo cáo
    reports = handle_command(transcript, data_file)

    st.write("📊 Kết quả báo cáo:")
    st.dataframe(reports)

    # Xuất Excel kết quả
    output_path = "/tmp/bao_cao.xlsx"
    reports.to_excel(output_path, index=False)

    with open(output_path, "rb") as f:
        st.download_button("⬇️ Tải báo cáo Excel", f, "bao_cao.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


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
