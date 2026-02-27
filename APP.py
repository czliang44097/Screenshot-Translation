import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# --- 頁面設定 ---
st.set_page_config(
    page_title="多模態截圖翻譯大師",
    page_icon="🏮",
    layout="wide"
)

# --- 初始化主題狀態 ---
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# --- 側邊欄：設定區 ---
with st.sidebar:
    st.title("⚙️ 設定面板")
    
    # 夜間模式切換按鈕
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
        ["一般", "韓文小說/網文", "遊戲截圖", "技術文件"],
        index=0
    )
    
    st.info("💡 提示：選擇正確的語境能顯著提升翻譯的自然度。")

# --- 動態 CSS 主題控制 ---
if st.session_state.dark_mode:
    # 深色模式 CSS
    theme_css = """
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stExpander {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 15px;
    }
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #f8fafc !important;
    }
    .stButton>button {
        background-color: #059669 !important;
        color: white !important;
        border: none;
    }
    div[data-testid="stExpander"] {
        background-color: #1e293b;
    }
    </style>
    """
else:
    # 淺色模式 CSS
    theme_css = """
    <style>
    .stApp {
        background-color: #f8fafc;
        color: #1e293b;
    }
    .stExpander {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 15px;
    }
    .stButton>button {
        background-color: #10b981 !important;
        color: white !important;
    }
    </style>
    """

st.markdown(theme_css, unsafe_allow_html=True)

# --- 主介面 ---
st.title("🏮 多模態截圖翻譯大師")
st.subheader("支援批量上傳與多語境優化的 OCR 翻譯工具")

# 檔案上傳
uploaded_files = st.file_uploader(
    "請上傳截圖 (最多 10 張)", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    if len(uploaded_files) > 10:
        st.warning("⚠️ 目前僅支援最多 10 張圖片，將只處理前 10 張。")
        uploaded_files = uploaded_files[:10]

    if st.button("🚀 開始翻譯"):
        if not api_key:
            st.error("❌ 請先在側邊欄輸入有效的 Gemini API 金鑰。")
        else:
            try:
                genai.configure(api_key=api_key)
                # 使用最新受支援的模型
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                base_instruction = "你是一個專業的翻譯專家。請先辨識圖片中的文字（OCR），然後將其翻譯成「繁體中文（台灣）」。\n"
                base_instruction += "輸出格式：僅輸出翻譯後的純文字，不要包含任何開場白或解釋。\n"
                
                if context == "韓文小說/網文":
                    base_instruction += "語境：韓文小說。請保持角色的對話語氣，使用台灣繁體中文的用語習慣，確保流暢且符合文學感。"
                elif context == "遊戲截圖":
                    base_instruction += "語境：遊戲截圖。請注意遊戲術語的一致性，翻譯應簡潔有力，適合遊戲介面顯示。"
                elif context == "技術文件":
                    base_instruction += "語境：技術文件。請確保專有名詞翻譯準確，語氣正式且嚴謹。"
                else:
                    base_instruction += "語境：一般。請提供準確且自然的翻譯。"

                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"正在處理第 {i+1}/{len(uploaded_files)} 張圖片：{uploaded_file.name}")
                    
                    img = Image.open(uploaded_file)
                    
                    response = model.generate_content([
                        base_instruction,
                        f"來源語言：{source_lang}。請翻譯這張圖片中的內容。",
                        img
                    ])
                    
                    with st.expander(f"🖼️ {uploaded_file.name} - 翻譯結果", expanded=True):
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.image(img, caption="原始圖片", use_container_width=True)
                        with col2:
                            st.markdown("**翻譯內容：**")
                            st.write(response.text)
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text("✅ 所有翻譯任務已完成！")
                st.balloons()

            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
                st.info("請檢查 API 金鑰是否正確。")

else:
    st.info("📸 請上傳圖片以開始翻譯任務。")
