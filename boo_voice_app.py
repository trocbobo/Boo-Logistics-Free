import streamlit as st
import pandas as pd
import requests
import os

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# ---- Nhận diện audio ----
def transcribe_audio(file):
    ext = file.name.split(".")[-1].lower()
    if ext == "mp3":
        ctype = "audio/mpeg"
    elif ext == "wav":
        ctype = "audio/wav"
    elif ext in ["m4a", "mp4"]:
        ctype = "audio/mp4"
    else:
        raise ValueError("Định dạng file không hỗ trợ")

    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}", "Content-Type": ctype}
    params = {"model": "nova-2", "language": "vi"}
    response = requests.post("https://api.deepgram.com/v1/listen",
                             headers=headers, params=params, data=file)
    return response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]

# ---- Hàm xuất báo cáo ----
def generate_revenue_report(data_file, month):
    df = pd.read_excel(data_file)
    df["Tháng"] = pd.to_datetime(df["Ngày"], errors="coerce").dt.month
    report = df[df["Tháng"] == month].groupby("Khách hàng")["Tổng VND"].sum().reset_index()
    out = f"Bao_cao_doanh_thu_T{month}.xlsx"
    report.to_excel(out, index=False)
    return out

def generate_cost_report(data_file, month
