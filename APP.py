import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import io

# --- 頁面設定 ---
st.set_page_config(
    page_title="多模態翻譯大師",
    page_icon="🏮",
    layout="wide"
)

# --- 初始化 Session State ---
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# 初始化 key，用於重置輸入元件
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

# --- 清空功能的回調函數 ---
def clear_content():
    st.session_state.reset_key += 1

# --- 側邊欄：設定區 ---
with st.sidebar:
    st.title("⚙️ 設定面板")
    
    # 工作模式選擇
    app_mode = st.radio(
        "選擇工作模式",
        ["📸 圖片截圖翻譯", "✍️ 純文字翻譯"],
        index=0
    )
    
    st.divider()
    
    # 夜間模式切換
    st.session_state.dark_mode = st.toggle("🌙 夜間模式", value=st.session_state.dark_mode)
    
    st.divider()
    
    api_key = st.text_input("請輸入 Gemini API 金鑰", type="password", help="請至 Google AI Studio 獲取金鑰")
    
    st.divider()
    
    source_lang = st.selectbox(
        "來源語言",
        ["自動偵測", "韓文", "日文", "英文", "簡體中文"],
        index=0
    )
    
    context = st.selectbox(
        "翻譯語境優化",
        ["一般", "小說/網文", "遊戲截圖", "技術文件"],
        index=0
    )
    
    st.info("💡 提示：選擇正確的語境能顯著提升翻譯的自然度。")

# --- 動態 CSS 主題控制 ---
theme_bg = "#0e1117" if st.session_state.dark_mode else "#f8fafc"
theme_text = "#ffffff" if st.session_state.dark_mode else "#1e293b"
expander_bg = "#1e293b" if st.session_state.dark_mode else "#ffffff"

theme_css = f"""
<style>
    .stApp {{ background-color: {theme_bg}; color: {theme_text}; }}
    .stExpander {{ background-color: {expander_bg} !important; border-radius: 15px; }}
    .stButton>button {{ background-color: #059669 !important; color: white !important; border: none; }}
    button[kind="secondary"] {{ background-color: #ef4444 !important; color: white !important; border: none !important; }}
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)

# --- 主介面 ---
st.title("🏮 多模態翻譯大師")
st.subheader(f"當前模式：{app_mode}")

# --- 翻譯邏輯封裝 ---
def run_translation(content_list):
    if not api_key:
        st.error("❌ 請先在側邊欄輸入有效的 Gemini API 金鑰。")
        return

    try:
        genai.configure(api_key=api_key)
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        model = genai.GenerativeModel('gemini-3-flash-preview')

        # 建立指令
        is_image = app_mode == "📸 圖片截圖翻譯"
        ocr_part = "請先辨識圖片中的文字（OCR），然後" if is_image else "請"
        base_instruction = f"你是一個專業的翻譯專家。{ocr_part}將其翻譯成「繁體中文（台灣）」。\n"
        base_instruction += "輸出格式：僅輸出翻譯後的純文字，不要包含任何開場白或解釋。\n"
        
        if context == "小說/網文":
            base_instruction += "語境：小說。請保持角色對話語氣，使用台灣繁體中文用語，確保流暢且符合文學感。"
        elif context == "遊戲截圖":
            base_instruction += "語境：遊戲。請注意術語一致性，翻譯應簡潔有力。"
        elif context == "技術文件":
            base_instruction += "語境：技術。確保專有名詞準確，語氣正式嚴謹。"
        else:
            base_instruction += "語境：一般。提供準確自然的翻譯。"

        # 圖片模式處理
        if is_image:
            progress_bar = st.progress(0)
            for i, uploaded_file in enumerate(content_list):
                img = Image.open(uploaded_file)
                with st.expander(f"🖼️ {uploaded_file.name} - 翻譯結果", expanded=True):
                    col_img, col_txt = st.columns([1, 1])
                    col_img.image(img, use_container_width=True)
                    with col_txt:
                        st.markdown("**翻譯內容：**")
                        response = model.generate_content([base_instruction, f"來源語言：{source_lang}", img], safety_settings=safety_settings)
                        if response.candidates[0].finish_reason in [3, 4, 8]:
                            st.warning("⚠️ 內容觸發安全過濾，無法完整輸出。")
                        st.write(response.text)
                progress_bar.progress((i + 1) / len(content_list))
        
        # 文字模式處理
        else:
            with st.status("正在翻譯中...", expanded=True):
                response = model.generate_content([base_instruction, f"來源語言：{source_lang}", content_list], safety_settings=safety_settings)
                st.markdown("### 📝 翻譯結果：")
                st.write(response.text)
        
        st.success("✅ 任務處理完成！")
        st.balloons()

    except Exception as e:
        st.error(f"❌ 發生錯誤：{str(e)}")

# --- UI 渲染控制 ---
if app_mode == "📸 圖片截圖翻譯":
    col_u, col_c = st.columns([3, 1])
    with col_u:
        uploaded_files = st.file_uploader(
            "請上傳截圖 (最多 10 張)", 
            type=["png", "jpg", "jpeg"], 
            accept_multiple_files=True,
            key=f"uploader_{st.session_state.reset_key}"
        )
    with col_c:
        st.write("") ; st.write("")
        if st.button("🗑️ 清空圖片", type="secondary", on_click=clear_content): pass

    if uploaded_files:
        if st.button("🚀 開始批量翻譯"):
            run_translation(uploaded_files[:10])
    else:
        st.info("📸 請上傳圖片以開始任務。")

else: # 純文字模式
    input_text = st.text_area(
        "請輸入要翻譯的原文內容：", 
        height=300, 
        placeholder="在此貼上文字...",
        key=f"text_{st.session_state.reset_key}"
    )
    col_btn1, col_btn2 = st.columns([1, 5])
    with col_btn1:
        start_btn = st.button("🚀 開始翻譯")
    with col_btn2:
        if st.button("🗑️ 清空文字", type="secondary", on_click=clear_content): pass

    if start_btn:
        if input_text.strip():
            run_translation(input_text)
        else:
            st.warning("⚠️ 請先輸入文字內容。")
