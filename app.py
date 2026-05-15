import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import os
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# APP CONFIG
# ─────────────────────────────────────────────────────────────────────────────

APP_TITLE = "🗺️ Cartographer Assistant"
APP_ICON = "🗺️"

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
st.title(APP_TITLE)
st.caption("AI-powered co-pilot for map design, symbology, and Egyptian GIS standards.")

# ─────────────────────────────────────────────────────────────────────────────
# MODELS & PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

PROVIDERS = {
    "Google Gemini": ["gemini-3.1-flash-lite", "gemini-3.1-pro", "gemini-2.5-flash"],
    "OpenRouter (Claude/Llama)": ["anthropic/claude-3.5-sonnet", "meta-llama/llama-3.1-405b", "openai/gpt-4o"]
}

SYSTEM_PROMPT_SUFFIX = (
    "\n\nCRITICAL RULES:\n"
    "1. Justify recommendations with cartographic principles (e.g., Visual Hierarchy).\n"
    "2. For Egypt, use EGSA 1907 (EPSG:22992/22993) and warn against EPSG:4326 for area tasks.\n"
    "3. If providing styling code (SLD/QML), include a version-compatibility warning.\n"
    "4. Analyze uploaded images for layout, contrast, and symbology."
)

SYSTEM_PROMPTS = {
    "General Cartography": "You are an expert cartographer guiding users on layout and projections." + SYSTEM_PROMPT_SUFFIX,
    "Symbology & Styling": "You are a specialist in vector/raster symbology (QML, SLD, Mapbox GL)." + SYSTEM_PROMPT_SUFFIX,
    "Egyptian GIS Context": "You specialize in Egyptian mapping, RTL labeling, and the Red/Blue/Purple Belts." + SYSTEM_PROMPT_SUFFIX,
    "Color Theory": "You are a color scientist. Suggest palettes based on ColorBrewer standards." + SYSTEM_PROMPT_SUFFIX,
    "Typography": "You are a cartographic typographer focusing on hierarchy and legibility." + SYSTEM_PROMPT_SUFFIX
}

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR - CONFIG & TOOLS
# ─────────────────────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("⚙️ Configuration")
    
    provider = st.selectbox("Select Provider", list(PROVIDERS.keys()))
    
    if provider == "Google Gemini":
        api_key = st.text_input("Gemini API Key", value=os.environ.get("GOOGLE_API_KEY", ""), type="password")
        model_id = st.selectbox("Model Selection", PROVIDERS["Google Gemini"])
    else:
        api_key = st.text_input("OpenRouter API Key", value=os.environ.get("OPENROUTER_API_KEY", ""), type="password")
        model_id = st.selectbox("Model Selection", PROVIDERS["OpenRouter (Claude/Llama)"])
    
    preset = st.selectbox("Specialty Preset", list(SYSTEM_PROMPTS.keys()))
    system_prompt = st.text_area("System Instruction", value=SYSTEM_PROMPTS[preset], height=150)
    temperature = st.slider("Temperature", 0.0, 1.5, 0.3, 0.1)
    
    st.divider()
    st.subheader("🖼️ Vision Input")
    uploaded_file = st.file_uploader("Upload map for critique", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Target Map", use_container_width=True)
    
    st.divider()
    st.subheader("💡 Quick Prompts")
    quick_queries = {
        "Nile Delta Palette": "Suggest a color palette for vegetation density in the Nile Delta.",
        "Egypt Belt Systems": "Explain when to use the Red Belt vs the Purple Belt in Egypt.",
        "Labeling Hierarchy": "Best practices for typographic hierarchy on a topographic map?",
        "CRS Warning": "Why avoid EPSG:4326 for area measurements in Egypt?"
    }
    
    for label, query in quick_queries.items():
        if st.button(label, use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": query})
            st.rerun()

    st.divider()
    # Dynamic Export & Clear (Visible only when chat is ready)
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        chat_export_md = f"# {APP_TITLE} Export\n\n"
        for m in st.session_state.messages:
            chat_export_md += f"**{m['role'].capitalize()}**: {m['content']}\n\n"
        
        st.download_button("📥 Download Chat (.md)", chat_export_md, "cartographer_chat.md", "text/markdown", use_container_width=True)
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# CHAT INTERFACE & LOGIC
# ─────────────────────────────────────────────────────────────────────────────

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Ask about map design...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_prompt = st.session_state.messages[-1]["content"]
    
    if not api_key:
        st.error("Missing API Key.")
        st.stop()

    with st.chat_message("assistant"):
        try:
            if provider == "Google Gemini":
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name=model_id, system_instruction=system_prompt)
                content = [last_prompt]
                if uploaded_file:
                    content.append(Image.open(uploaded_file))
                
                response = model.generate_content(content, stream=True, generation_config={"temperature": temperature})
                full_response = st.write_stream(chunk.text for chunk in response)
                if hasattr(response, 'usage_metadata'):
                    m = response.usage_metadata
                    st.caption(f"Tokens: {m.total_token_count}")

            else: # OpenRouter
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
                messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                response = client.chat.completions.create(model=model_id, messages=messages, stream=True, temperature=temperature)
                full_response = st.write_stream(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content)

            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")