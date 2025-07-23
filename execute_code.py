import streamlit as st
import json
import os
import requests
import pandas as pd
from dotenv import load_dotenv

# ── Load .env and API key ──────────────────────────────
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error(" GEMINI_API_KEY not found in .env file.")
    st.stop()

# ── Load parcel_data from logs.json ────────────────────
try:
    with open("logs.json", "r") as f:
        parcel_data = json.load(f)
    sample_parcel = parcel_data[0]
except Exception as e:
    st.error(f"Failed to load logs.json: {e}")
    st.stop()


# ── Gemini API interaction ─────────────────────────────
def get_code_from_llm(query: str, sample_parcel):
    prompt = f"""
You are a Python data assistant. Below is the structure of a single parcel tracking log:

{json.dumps(sample_parcel, indent=2)}n

The data you will be analyzing is a Python list named `parcel_data`, where each element follows the above structure.

Generate Python code to answer the user query. Only return a JSON object with:
- "explanation": explanation of how the query will be answered
- "code": Python code to produce the answer and store it in a variable named `result`

User query: {query}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
    )

    res_json = response.json()
    if "candidates" not in res_json:
        return None, None, f"   Gemini API Error: {json.dumps(res_json, indent=2)}"

    raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]

    try:
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        clean_json = raw_text[start:end]
        response_dict = json.loads(clean_json)
    except Exception as e:
        return None, None, f" Failed to parse Gemini response: {e}"

    return response_dict.get("explanation"), response_dict.get("code"), None



def execute_generated_code(code: str, parcel_data: list):
    local_vars = {"parcel_data": parcel_data, "pd": pd}

    
    safe_code = (
        code.replace("null", "None")
            .replace("false", "False")
            .replace("true", "True")
    )

    try:
        exec(safe_code, {}, local_vars)
        return local_vars.get("result"), None
    except Exception as e:
        return None, f" Code execution error: {e}"



st.set_page_config(page_title="Parcel Chat Assistant", layout="centered")
st.title("📦Parcel Chat Assistant 🤖")

if "messages" not in st.session_state:
    st.session_state.messages = []


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


query = st.chat_input(" Ask a question about parcel data...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner(" Thinking..."):
            explanation, code, err = get_code_from_llm(query, sample_parcel)

        if err:
            st.error(err)
            st.session_state.messages.append({"role": "assistant", "content": err})
        elif code:
            result, exec_err = execute_generated_code(code, parcel_data)

            if exec_err:
                st.error(exec_err)
                st.session_state.messages.append({"role": "assistant", "content": exec_err})
            else:
                
                st.markdown(f"** Explanation:** {explanation}")
                st.code(code, language="python")
                st.markdown("** Result:**")
                st.write(result)

            
                response_md = f"** Explanation:**\n{explanation}\n\n** Result:**\n{result}"
                st.session_state.messages.append({"role": "assistant", "content": response_md})
        else:
            st.warning(" Could not get a valid response from Gemini.")
            st.session_state.messages.append({"role": "assistant", "content": " No valid response received."})
