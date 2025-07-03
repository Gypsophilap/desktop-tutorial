import streamlit as st
import requests
from pathlib import Path
import os

API_KEY = "YourAPI"
API_URL = "APIURL"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}
# 页面设置
st.set_page_config(page_title="DeepSeekChat", layout="wide")

background_image_url = "https://raw.githubusercontent.com/Gypsophilap/desktop-tutorial/main/bg2.jpg"

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("{background_image_url}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

def call_deepseek(messages):
    payload = {
        "model": "deepseek-r1",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 10000
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()  # 这会抛出HTTP错误异常
        
        result = response.json()
        # 尝试两种可能的响应格式
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        elif "output" in result:  # 有些API可能有不同的结构
            return result["output"]["text"]
        else:
            return str(result)  # 返回原始响应用于调试
    except requests.exceptions.RequestException as e:
        return f"请求失败: {str(e)}"
    except Exception as e:
        return f"处理响应时出错: {str(e)}"

def call_deepseek_stream(messages):
    payload = {
        "model": "deepseek-r1",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 10000,
        "stream": True
    }
    try:
        with requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=60) as response:
            response.raise_for_status()
            buffer = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        result = __import__('json').loads(data)
                        # 兼容OpenAI格式
                        delta = result.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            buffer += content
                            yield buffer
                    except Exception:
                        continue
    except requests.exceptions.RequestException as e:
        yield f"请求失败: {str(e)}"
    except Exception as e:
        yield f"处理响应时出错: {str(e)}"

st.title("DeepSeek-R1")

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入
user_input = st.chat_input("请输入你的问题...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # AI 回复（流式）
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            placeholder = st.empty()
            reply = ""
            for partial in call_deepseek_stream(st.session_state.messages):
                reply = partial
                placeholder.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
