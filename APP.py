import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import io

# --- 頁面設定 ---
st.set_page_config(
    page_title="多模態截圖翻譯大師",
    page_icon="🏮",
    layout="wide"
)

# --- 初始化 Session State ---
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# 初始化 file_uploader 的 key，用於重置元件
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# --- 清空檔案的回調函數 ---
def clear_files():
    st.session_state.uploader_key += 1

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
        ["一般", "小說/網文", "遊戲截圖", "技術文件"],
        index=0
    )
    
    st.info("💡 提示：選擇正確的語境能顯著提升翻譯的自然度。")

# --- 動態 CSS 主題控制 ---
if st.session_state.dark_mode:
    theme_css = """
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stExpander { background-color: #1e293b !important; border: 1px solid #334155 !important; border-radius: 15px; }
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: #f8fafc !important; }
    .stButton>button { background-color: #059669 !important; color: white !important; border: none; }
    div[data-testid="stExpander"] { background-color: #1e293b; }
    button[kind="secondary"] { background-color: #ef4444 !important; color: white !important; border: none !important; }
    </style>
    """
else:
    theme_css = """
    <style>
    .stApp { background-color: #f8fafc; color: #1e293b; }
    .stExpander { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 15px; }
    .stButton>button { background-color: #10b981 !important; color: white !important; }
    button[kind="secondary"] { background-color: #fee2e2 !important; color: #ef4444 !important; border: 1px solid #fecaca !important; }
    button[kind="secondary"]:hover { background-color: #fecaca !important; }
    </style>
    """

st.markdown(theme_css, unsafe_allow_html=True)

# --- 主介面 ---
st.title("🏮 多模態截圖翻譯大師")
st.subheader("支援批量上傳與多語境優化的 OCR 翻譯工具")

# 檔案上傳區域
col1, col2 = st.columns([3, 1])
with col1:
    uploaded_files = st.file_uploader(
        "請上傳截圖 (最多 10 張)", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}"
    )
with col2:
    st.write("") 
    st.write("") 
    if st.button("🗑️ 一鍵清空", type="secondary", on_click=clear_files):
        pass

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
                
                # 解除安全過濾限制，避免 finish_reason: 8 的問題
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
                
                model = genai.GenerativeModel('gemini-3-flash-preview') 
                
                base_instruction = "你是一個專業的翻譯專家。請先辨識圖片中的文字（OCR），然後將其翻譯成「繁體中文（台灣）」。\n"
                base_instruction += "輸出格式：僅輸出翻譯後的純文字，不要包含任何開場白或解釋。\n"
                
                if context == "小說/網文":
                    base_instruction += "語境：小說。請保持角色對話語氣，使用台灣繁體中文用語，確保流暢且符合文學感。"
                elif context == "遊戲截圖":
                    base_instruction += "語境：遊戲。請注意遊戲術語一致性，翻譯應簡潔有力。"
                elif context == "技術文件":
                    base_instruction += "語境：技術。確保專有名詞準確，語氣正式嚴謹。"
                else:
                    base_instruction += "語境：一般。提供準確自然的翻譯。"

                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"正在處理第 {i+1}/{len(uploaded_files)} 張：{uploaded_file.name}")
                    
                    img = Image.open(uploaded_file)
                    
                    with st.expander(f"🖼️ {uploaded_file.name} - 翻譯結果", expanded=True):
                        col_img, col_txt = st.columns([1, 1])
                        with col_img:
                            st.image(img, caption="原始圖片", use_container_width=True)
                        
                        with col_txt:
                            st.markdown("**翻譯內容：**")
                            try:
                                # 調用 API 並套用安全設定
                                response = model.generate_content(
                                    [base_instruction, f"來源語言：{source_lang}", img],
                                    safety_settings=safety_settings
                                )
                                
                                # 檢查是否被安全機制攔截 (finish_reason 3=SAFETY, 8=OTHER/FILTER)
                                if response.candidates[0].finish_reason in [3, 4, 8]:
                                    st.warning("⚠️ 該圖片內容觸發了 AI 安全過濾機制（可能是敏感詞彙），無法完整輸出。")
                                    # 嘗試讀取部分內容（如果有）
                                    try:
                                        st.write(response.text)
                                    except:
                                        st.info("無法顯示翻譯結果。")
                                else:
                                    st.write(response.text)
                                    
                            except Exception as api_err:
                                # 針對 finish_reason 導致的 response.text 錯誤進行捕獲
                                if "finish_reason" in str(api_err):
                                    st.error("❌ 翻譯被攔截：內容可能包含敏感描述，請調整語境或圖片再試。")
                                else:
                                    st.error(f"❌ API 調用出錯：{str(api_err)}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text("✅ 所有翻譯任務已完成！")
                st.balloons()

            except Exception as e:
                st.error(f"❌ 系統錯誤：{str(e)}")
                st.info("請檢查 API 金鑰或網路連線。")

else:
    st.info("📸 請上傳圖片以開始翻譯任務。")
