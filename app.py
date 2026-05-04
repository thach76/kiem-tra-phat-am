import streamlit as st
from streamlit_mic_recorder import mic_recorder
import whisper
from pypinyin import pinyin, Style
from hanziconv import HanziConv
from deep_translator import GoogleTranslator
import pandas as pd
import io
import os
import time
import string
import csv
import base64
import edge_tts
import asyncio

st.set_page_config(page_title="Hệ Thống Kiểm Tra Phát Âm", layout="wide")

# --- 0. QUẢN LÝ THƯ MỤC & DỌN RÁC (GARBAGE COLLECTION) ---
TTS_DIR = "tts_cache"
os.makedirs(TTS_DIR, exist_ok=True)
os.makedirs("sounds", exist_ok=True) # Đảm bảo thư mục sounds luôn tồn tại

# Chỉ dọn rác 1 lần duy nhất mỗi khi mở app (phiên làm việc mới)
if 'cleanup_done' not in st.session_state:
    for filename in os.listdir(TTS_DIR):
        filepath = os.path.join(TTS_DIR, filename)
        try:
            if os.path.isfile(filepath):
                os.remove(filepath)
        except Exception:
            pass
    st.session_state.cleanup_done = True

# --- 1. KHỞI TẠO BỘ NHỚ ---
if 'processed_audio_id' not in st.session_state: st.session_state.processed_audio_id = None
if 'dictated_audio_id' not in st.session_state: st.session_state.dictated_audio_id = None
if 'target_text_memory' not in st.session_state: st.session_state.target_text_memory = ""
if 'analysis_result' not in st.session_state: st.session_state.analysis_result = None
if 'dictated_text' not in st.session_state: st.session_state.dictated_text = ""

# --- 2. HỆ THỐNG TẢI DỮ LIỆU ---
@st.cache_resource
def load_model():
    return whisper.load_model("base")

@st.cache_data
def load_csv_data(filepath):
    data_dict = {}
    if os.path.exists(filepath):
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                key_col = reader.fieldnames[0]
                for row in reader: data_dict[row[key_col]] = row
    return data_dict

model = load_model()
feedbacks = load_csv_data("feedback.csv")
vocab_dict = load_csv_data("vocab.csv")

# --- 3. HỆ THỐNG ÂM THANH ---
def play_sound_effect_hidden(score):
    sound_file = "sounds/perfect.mp3" if score == 100 else ("sounds/good.mp3" if score >= 50 else "sounds/bad.mp3")
    if os.path.exists(sound_file):
        with open(sound_file, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)

async def _generate_tts(text, voice, rate, filepath):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(filepath)

def create_ai_voice(text, voice, rate="+0%"):
    file_hash = hash(text + voice + rate)
    # Lưu vào thư mục tts_cache thay vì thư mục gốc
    filepath = os.path.join(TTS_DIR, f"tts_{abs(file_hash)}.mp3")
    
    if not os.path.exists(filepath):
        try: loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate_tts(text, voice, rate, filepath))
    return filepath

# --- 4. CÁC HÀM XỬ LÝ LÕI ---
def get_chinese_details(text):
    res = pinyin(text, style=Style.TONE3)
    parsed = []
    for item in res:
        p = item[0].lower()
        if p[-1].isdigit(): parsed.append((p[:-1], p[-1]))
        else:
            if p not in string.punctuation and p.strip(): parsed.append((p, "5"))
    return parsed

def clean_english_text(text):
    text = text.translate(str.maketrans('', '', string.punctuation)).lower()
    return text.split()

def analyze_pronunciation(target, user, lang):
    html_output, errors_found, correct_count = [], set(), 0
    if lang == "Tiếng Trung":
        target_info, user_info = get_chinese_details(target), get_chinese_details(user)
        total_count = len(target_info)
        for i in range(total_count):
            t_pinyin, t_tone = target_info[i]
            char = target[i]
            if i >= len(user_info):
                html_output.append(f"<span style='color:gray; font-size:24px; margin:5px;'>{char} (Thiếu)</span>")
                errors_found.add("missing")
                continue
            u_pinyin, u_tone = user_info[i]
            if t_pinyin == u_pinyin and t_tone == u_tone:
                color, label = "#28a745", "Đúng"
                correct_count += 1
            elif t_pinyin == u_pinyin and t_tone != u_tone:
                color, label = "#ffc107", f"Sai thanh {u_tone}"
                errors_found.add(f"tone_{t_tone}")
            else:
                color, label = "#dc3545", "Sai âm"
                errors_found.add("wrong_pinyin")
            html_output.append(f"<div style='display:inline-block; text-align:center; margin:10px;'><div style='font-size:30px; color:{color}; font-weight:bold;'>{char}</div><div style='font-size:14px; color:gray;'>{t_pinyin}{t_tone}</div><div style='font-size:12px; background-color:{color}; color:white; border-radius:5px; padding:2px 5px;'>{label}</div></div>")
    else:
        target_words, user_words = clean_english_text(target), clean_english_text(user)
        total_count = len(target_words)
        for i in range(total_count):
            target_w = target_words[i]
            if i >= len(user_words):
                html_output.append(f"<div style='display:inline-block; text-align:center; margin:10px;'><div style='font-size:24px; color:gray; text-decoration: line-through;'>{target_w}</div><div style='font-size:12px; background-color:gray; color:white; border-radius:5px; padding:2px 5px;'>Thiếu</div></div>")
                errors_found.add("missing")
                continue
            user_w = user_words[i]
            if target_w == user_w:
                color, label = "#28a745", "Đúng"
                correct_count += 1
            else:
                color, label = "#dc3545", f"Nghe ra: {user_w}"
                errors_found.add("english_wrong")
            html_output.append(f"<div style='display:inline-block; text-align:center; margin:10px;'><div style='font-size:24px; color:{color}; font-weight:bold;'>{target_w}</div><div style='font-size:12px; background-color:{color}; color:white; border-radius:5px; padding:2px 5px;'>{label}</div></div>")

    score = int((correct_count / total_count) * 100) if total_count > 0 else 0
    return "".join(html_output), score, errors_found

# --- 5. GIAO DIỆN & LOGIC ĐIỀU HƯỚNG ---
st.title("🎙️ Hệ Thống Kiểm Tra Phát Âm PRO")

with st.sidebar:
    st.header("⚙️ Thiết lập hệ thống")
    app_mode = st.selectbox("Chế độ hoạt động:", ["Luyện tập tự do", "Làm bài kiểm tra (Excel)"])
    lang_choice = st.radio("Ngôn ngữ:", ("Tiếng Trung", "Tiếng Anh"))
    
    char_type = "Giản thể"
    if lang_choice == "Tiếng Trung":
        char_type = st.radio("Loại chữ:", ("Giản thể", "Phồn thể"))
        voice_choice = st.selectbox("Giọng AI bản xứ:", ["👩 Nữ (Xiaoxiao - Truyền cảm)", "👦 Nam (Yunxi - Trầm ấm)"])
        voice_code = "zh-CN-XiaoxiaoNeural" if "Nữ" in voice_choice else "zh-CN-YunxiNeural"
        whisper_lang = "zh"
    else:
        voice_choice = st.selectbox("Giọng AI bản xứ:", ["👩 Nữ (Aria)", "👦 Nam (Guy)"])
        voice_code = "en-US-AriaNeural" if "Nữ" in voice_choice else "en-US-GuyNeural"
        whisper_lang = "en"

target_text = ""

# --- CHẾ ĐỘ 1: LUYỆN TẬP TỰ DO ---
if app_mode == "Luyện tập tự do":
    st.write("### 📝 Nhập dữ liệu")
    col_text, col_mic = st.columns([4, 1])
    with col_mic:
        st.write("Hoặc đọc để nhập:")
        dictate_audio = mic_recorder(start_prompt="🎤 Bấm nói", stop_prompt="⏹ Dừng", key='dictate_recorder')
        if dictate_audio and dictate_audio['id'] != st.session_state.dictated_audio_id:
            with st.spinner("Đang chuyển giọng..."):
                temp_dict_file = f"temp_dict_{int(time.time())}.wav"
                with open(temp_dict_file, "wb") as f: f.write(dictate_audio['bytes'])
                try:
                    res_dict = model.transcribe(temp_dict_file, language=whisper_lang)
                    st.session_state.dictated_text = res_dict['text']
                    st.session_state.dictated_audio_id = dictate_audio['id']
                except Exception as e: st.error(e)
                if os.path.exists(temp_dict_file): os.remove(temp_dict_file)
                st.rerun()

    with col_text:
        default_val = st.session_state.dictated_text if st.session_state.dictated_text else ("你好" if lang_choice == "Tiếng Trung" else "I should study every day")
        raw_input_text = st.text_input("Nhập câu cần luyện:", value=default_val)

    if lang_choice == "Tiếng Trung" and raw_input_text:
        target_text = HanziConv.toTraditional(raw_input_text) if char_type == "Phồn thể" else HanziConv.toSimplified(raw_input_text)
    else:
        target_text = raw_input_text

# --- CHẾ ĐỘ 2: LÀM BÀI TỪ EXCEL ---
elif app_mode == "Làm bài kiểm tra (Excel)":
    st.write("### 📁 Đọc dữ liệu kiểm tra")
    uploaded_file = st.file_uploader("Tải lên file (.xlsx hoặc .csv) - Cần có cột 'Cau_Hoi'", type=['xlsx', 'csv'])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            if 'Cau_Hoi' in df.columns:
                question_list = df['Cau_Hoi'].dropna().astype(str).tolist()
                raw_input_text = st.selectbox("Chọn câu hỏi để thực hành:", question_list)
                if lang_choice == "Tiếng Trung" and raw_input_text:
                    target_text = HanziConv.toTraditional(raw_input_text) if char_type == "Phồn thể" else HanziConv.toSimplified(raw_input_text)
                else:
                    target_text = raw_input_text
            else:
                st.error("Lỗi: Không tìm thấy cột 'Cau_Hoi'.")
        except Exception as e: st.error(f"Lỗi đọc file: {e}")

# --- TIẾN HÀNH KIỂM TRA ---
if target_text != st.session_state.target_text_memory:
    st.session_state.target_text_memory = target_text
    st.session_state.analysis_result = None

if target_text:
    st.write("---")
    st.write("🔊 **Nghe AI đọc mẫu:**")
    col_play_normal, col_play_slow, col_empty = st.columns([1, 1, 2])
    with col_play_normal:
        st.caption("🚀 Tốc độ bình thường")
        normal_audio = create_ai_voice(target_text, voice_code, rate="+0%")
        st.audio(normal_audio, format='audio/mp3')
    with col_play_slow:
        st.caption("🐢 Tốc độ chậm (Từng từ)")
        slow_audio = create_ai_voice(target_text, voice_code, rate="-40%")
        st.audio(slow_audio, format='audio/mp3')

    st.write("---")
    st.write("🎙️ **Đến lượt bạn:**")
    test_audio_data = mic_recorder(start_prompt="🔴 Bấm để nộp bài", stop_prompt="⏹️ Dừng & Chấm Điểm", key='test_recorder')

    if test_audio_data:
        current_audio_id = test_audio_data['id']
        if current_audio_id != st.session_state.processed_audio_id:
            with st.spinner("Đang soi lỗi bằng AI..."):
                unique_filename = f"temp_test_{int(time.time())}.wav"
                with open(unique_filename, "wb") as f: f.write(test_audio_data['bytes'])
                try:
                    result = model.transcribe(unique_filename, language=whisper_lang, temperature=0.0)
                    user_text = result['text']
                    html_res, score, errors = analyze_pronunciation(target_text, user_text, lang_choice)
                    translated_text = GoogleTranslator(source='auto', target='vi').translate(target_text)

                    st.session_state.analysis_result = {
                        'html': html_res, 'score': score, 'errors': errors,
                        'user_text': user_text, 'audio_bytes': test_audio_data['bytes'],
                        'translated_text': translated_text
                    }
                    st.session_state.processed_audio_id = current_audio_id
                except Exception as e: st.error(f"Lỗi: {e}")
                try:
                    if os.path.exists(unique_filename): os.remove(unique_filename)
                except: pass

# --- 6. HIỂN THỊ KẾT QUẢ ---
if st.session_state.analysis_result:
    res = st.session_state.analysis_result
    play_sound_effect_hidden(res['score'])
    
    st.write("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("### Phân tích chi tiết:")
        st.markdown(res['html'], unsafe_allow_html=True)
        
        st.write("🎧 **Nghe lại giọng của bạn:**")
        st.audio(res['audio_bytes'], format='audio/wav')
        st.caption(f"Máy nghe được thành: *{res['user_text']}*")
        
        st.write("---")
        st.write(f"📖 **Dịch nghĩa:** {res['translated_text']}")
        
        if lang_choice == "Tiếng Trung":
            st.write("🔍 **Phân tích từ vựng:**")
            for char in target_text:
                search_char = HanziConv.toSimplified(char) 
                if search_char in vocab_dict:
                    v_info = vocab_dict[search_char]
                    st.write(f"- **{char}** (Hán Việt: *{v_info.get('hanviet', '')}*): {v_info.get('meaning', '')}")
    
    with col2:
        color = "green" if res['score'] >= 80 else ("orange" if res['score'] >= 50 else "red")
        st.markdown(f"<div style='text-align:center; padding:20px; border:2px solid {color}; border-radius:10px; margin-bottom: 20px;'><h3 style='margin:0;'>Điểm số</h3><h1 style='color:{color}; font-size:48px; margin:0;'>{res['score']}%</h1></div>", unsafe_allow_html=True)
        
        if res['errors']:
            st.write("💡 **Gợi ý sửa lỗi:**")
            for err in res['errors']:
                if err in feedbacks: st.warning(feedbacks[err].get('message', ''))