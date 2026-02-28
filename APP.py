import streamlit as st
from PIL import Image
import io
import base64
import litellm
from litellm import completion

# --- 頁面設定 ---
st.set_page_config(
    page_title="萬能多模態翻譯大師",
    page_icon="🏮",
    layout="wide"
)

# --- 初始化 Session State ---
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

def clear_files():
    st.session_state.uploader_key += 1

# --- 側邊欄：設定區 ---
with st.sidebar:
    st.title("⚙️ 設定面板")
    st.session_state.dark_mode = st.toggle("🌙 夜間模式", value=st.session_state.dark_mode)
    st.divider()

    # 1. 選擇模型供應商
    provider = st.selectbox(
        "選擇 AI 供應商",
        ["Google (Gemini)", "OpenAI", "Anthropic", "xAI (Grok)"]
    )

    # 2. 根據供應商動態設定模型名稱
    model_map = {
        "Google (Gemini)": "gemini/gemini-3-flash-preview",
        "OpenAI": "openai/gpt-5-mini",
        "Anthropic": "anthropic/claude-4.5-haiku",
        "xAI (Grok)": "xai/grok-3-mini"
    }
    selected_model = model_map[provider]
    st.caption(f"當前模型: `{selected_model}`")

    # 3. API Key 輸入
    api_key = st.text_input(f"請輸入 {provider} API 金鑰", type="password")
    
    st.divider()
    source_lang = st.selectbox("來源語言", ["自動偵測", "韓文", "日文", "英文", "簡體中文"])
    context = st.selectbox("翻譯語境優化", ["一般", "小說/網文", "遊戲截圖", "技術文件"])

# --- 圖片處理工具 ---
def encode_image(image):
    """將 PIL 圖片轉換為 Base64 字串"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 動態 CSS (維持原樣) ---
theme_css = f"""
<style>
.stApp {{ background-color: {'#0e1117' if st.session_state.dark_mode else '#f8fafc'}; color: {'#ffffff' if st.session_state.dark_mode else '#1e293b'}; }}
.stExpander {{ background-color: {'#1e293b' if st.session_state.dark_mode else '#ffffff'} !important; border-radius: 15px; }}
button[kind="secondary"] {{ background-color: #ef4444 !important; color: white !important; }}
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)

# --- 主介面 ---
st.title("🏮 萬能多模態翻譯大師")
st.subheader(f"目前驅動：{provider}")

uploaded_files = st.file_uploader(
    "請上傳截圖 (最多 10 張)", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}"
)

if st.button("🗑️ 一鍵清空", type="secondary", on_click=clear_files):
    pass

if uploaded_files:
    if len(uploaded_files) > 10:
        uploaded_files = uploaded_files[:10]

    if st.button("🚀 開始翻譯"):
        if not api_key:
            st.error(f"❌ 請輸入 {provider} 的 API 金鑰！")
        else:
            # 設定提示詞
            base_instruction = f"你是一個專業的翻譯專家。請 OCR 辨識圖片中的{source_lang}文字，並翻譯成「繁體中文（台灣）」。\n"
            base_instruction += "輸出格式：僅輸出翻譯後的純文字內容，絕對不要包含任何開場白、備註或解釋。\n"
            
            if context == "小說/網文":
                base_instruction += "語境：小說。請保持角色對話語氣，確保流暢且符合台灣文學感。"
            elif context == "遊戲截圖":
                base_instruction += "語境：遊戲。請注意術語一致性，簡潔有力。"
            
            progress_bar = st.progress(0)
            
            for i, uploaded_file in enumerate(uploaded_files):
                img = Image.open(uploaded_file)
                base64_image = encode_image(img)
                
                with st.expander(f"🖼️ {uploaded_file.name}", expanded=True):
                    col_img, col_txt = st.columns([1, 1])
                    col_img.image(img, use_container_width=True)
                    
                    with col_txt:
                        st.markdown("**翻譯內容：**")
                        try:
                            # 使用 LiteLLM 統一呼叫
                            # 針對 Gemini，我們額外傳入安全設定
                            extra_kwargs = {}
                            if "gemini" in selected_model:
                                extra_kwargs["safety_settings"] = [
                                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                                ]

                            response = completion(
                                model=selected_model,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": base_instruction},
                                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                                        ]
                                    }
                                ],
                                api_key=api_key,
                                **extra_kwargs
                            )
                            
                            translated_text = response.choices[0].message.content
                            st.write(translated_text)
                            
                        except Exception as e:
                            st.error(f"❌ 翻譯出錯：{str(e)}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            st.success("✅ 翻譯完成！")
            st.balloons()
else:
    st.info("📸 請上傳圖片開始。")
