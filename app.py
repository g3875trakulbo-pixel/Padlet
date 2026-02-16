import streamlit as st
import pandas as pd
import re
import os
import io
from datetime import datetime

# --- 1. การตั้งค่าหน้าเว็บและสไตล์ (Theme สีเขียว Dashboard) ---
st.set_page_config(page_title="ระบบตรวจสอบงาน - ครูตระกูล", layout="centered")

# สร้างโฟลเดอร์เก็บฐานข้อมูลไฟล์ (จำลองประวัติการอัปโหลด)
DB_DIR = "stored_db"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

st.markdown("""
    <style>
    .main-header {
        background-color:#1b5e20; padding:35px; border-radius:20px; 
        text-align:center; color:white; border: 3px solid #ffffff; 
        box-shadow: 0px 10px 20px rgba(0,0,0,0.2);
    }
    .stDataFrame { border: 1px solid #e0e0e0; border-radius: 10px; }
    </style>
    <div class="main-header">
        <h1 style="margin:0; font-family: 'Sarabun', sans-serif;">📋 ระบบตรวจสอบการส่งงาน</h1>
        <p style="margin-top:10px; font-size:1.2rem;">จัดการฐานข้อมูลและเช็คสถานะรายบุคคล</p>
        <hr style="border: 0.5px solid #fff; width: 30%; margin: 15px auto;">
        <p style="font-size
