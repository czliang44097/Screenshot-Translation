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

# --- 自定義 CSS ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #10b981;
        color: white;
        font-weight: bold;
    }
    .stExpander {
        background-color: white;
        border-radius: 15px;
        border: 1px solid #e5e7eb;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 側邊欄：設定區 ---
with st.sidebar:
    st.title("⚙️ 設定面板")
    
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
            # 初始化 Gemini
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                # 動態調整 System Prompt
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

                # 進度條
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 處理每一張圖片
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"正在處理第 {i+1}/{len(uploaded_files)} 張圖片：{uploaded_file.name}")
                    
                    # 讀取圖片
                    img = Image.open(uploaded_file)
                    
                    # 呼叫 Gemini
                    response = model.generate_content([
                        base_instruction,
                        f"來源語言：{source_lang}。請翻譯這張圖片中的內容。",
                        img
                    ])
                    
                    # 顯示結果
                    with st.expander(f"🖼️ {uploaded_file.name} - 翻譯結果", expanded=True):
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.image(img, caption="原始圖片", use_container_width=True)
                        with col2:
                            st.markdown("**翻譯內容：**")
                            st.write(response.text)
                            if st.button(f"複製內容", key=f"copy_{i}"):
                                st.write("已顯示於上方，請手動選取複製。") # Streamlit 原生不支援 JS 複製，此為提示
                    
                    # 更新進度
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text("✅ 所有翻譯任務已完成！")
                st.balloons()

            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
                st.info("請檢查 API 金鑰是否正確，或網路連線是否正常。")

else:
    st.info("📸 請上傳圖片以開始翻譯任務。")

# --- 部署說明 ---
# 1. 將此代碼儲存為 app.py
# 2. 建立 requirements.txt 並加入以下內容：
#    streamlit
#    google-generativeai
#    Pillow
# 3. 上傳至 GitHub 並在 Streamlit Cloud 連結此倉庫即可部署。
