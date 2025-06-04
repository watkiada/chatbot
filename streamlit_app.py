"""Streamlit interface for the WatkiBot legal assistant."""

import re
import time
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="WatkiBot", page_icon="⚖️", layout="centered")

# Custom styles for chat bubbles
st.markdown(
    """
    <style>
    .chat-bubble {
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        max-width: 80%;
        font-size: 16px;
    }
    .user-bubble { background-color: #343541; float: right; text-align: right; color: white; }
    .bot-bubble { background-color: #444654; float: left; text-align: left; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Gather API key from Streamlit secrets or user input
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if not openai_api_key:
    openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please provide an OpenAI API key to continue.", icon="🗝️")
    st.stop()

client = OpenAI(api_key=openai_api_key)
ASSISTANT_ID = st.secrets.get("ASSISTANT_ID", "asst_QD4XWA2zINlHoh8llg7jcbpK")

TIMEOUT = 60
SLEEP_SECS = 1

# Available cases
case_list = [
    "Ortiz, Margarita",
    "Newman, Al",
    "Kelvin, Douglas",
    "Jungk, Heidi",
    "Gomez, Juan",
    "Ferguson, Robert",
    "Curnow, Robert",
    "Adams, Guy",
]

# Session state stores a mapping from case name to its messages and thread id
if "cases" not in st.session_state:
    st.session_state.cases = {}

# Currently selected case
def init_case(case_name: str) -> None:
    """Create storage and an OpenAI thread for the given case if needed."""

    if case_name not in st.session_state.cases:
        thread = client.beta.threads.create()
        st.session_state.cases[case_name] = {
            "thread_id": thread.id,
            "messages": [],
        }

if "selected_case" not in st.session_state:
    st.session_state.selected_case = case_list[0]
init_case(st.session_state.selected_case)


# Helper to send a message to OpenAI using the thread for the selected case

def send_message(case_name: str, content: str) -> str:
    """Send a user message and return the assistant reply for the case."""

    case = st.session_state.cases[case_name]

    client.beta.threads.messages.create(
        thread_id=case["thread_id"],
        role="user",
        content=content,
    )

    run = client.beta.threads.runs.create(
        thread_id=case["thread_id"], assistant_id=ASSISTANT_ID
    )

    start = time.time()
    while time.time() - start < TIMEOUT:
        status = client.beta.threads.runs.retrieve(
            thread_id=case["thread_id"], run_id=run.id
        )
        if status.status == "completed":
            messages = client.beta.threads.messages.list(
                thread_id=case["thread_id"], order="desc", limit=1
            )
            for msg in messages.data:
                if msg.role == "assistant":
                    response = " ".join(
                        part.text.value for part in msg.content if part.type == "text"
                    )
                    cleaned = re.sub(r"【\d+:\d+†source】", "", response).strip()
                    return cleaned
        elif status.status == "failed":
            return "❌ WatkiBot failed to respond. Please retry."
        time.sleep(SLEEP_SECS)
    return "❌ WatkiBot timed out. Please retry."


# Sidebar with case selection and quick actions
with st.sidebar:
    st.header("🗂️ Client Tools")
    selected = st.selectbox(
        "Select Client", case_list, index=case_list.index(st.session_state.selected_case)
    )
    if selected != st.session_state.selected_case:
        st.session_state.selected_case = selected
        init_case(selected)
        st.rerun()

    if st.button("🩺 Summarize Medical Reports"):
        st.session_state.cases[selected]["messages"].append(
            {"role": "user", "content": f"Summarize medical reports for {selected}"}
        )
        st.rerun()

    if st.button("💥 List Key Injuries"):
        st.session_state.cases[selected]["messages"].append(
            {"role": "user", "content": f"List all known injuries for {selected}"}
        )
        st.rerun()

    if st.button("📄 Suggest Stipulations"):
        st.session_state.cases[selected]["messages"].append(
            {
                "role": "user",
                "content": f"Suggest WCAB stipulations for {selected} including PD rating",
            }
        )
        st.rerun()


# Display messages for the current case
for message in st.session_state.cases[st.session_state.selected_case]["messages"]:
    style = "user-bubble" if message["role"] == "user" else "bot-bubble"
    icon = "👨‍⚖️" if message["role"] == "user" else "⚖️"
    st.markdown(
        f"<div class='chat-bubble {style}'>{icon}<br>{message['content']}</div>",
        unsafe_allow_html=True,
    )

# Input from user
prompt = st.chat_input("Ask WatkiBot something...")
if prompt:
    st.session_state.cases[st.session_state.selected_case]["messages"].append(
        {"role": "user", "content": prompt}
    )
    st.rerun()

# If last message is from user, generate response
case_data = st.session_state.cases[st.session_state.selected_case]
if case_data["messages"] and case_data["messages"][-1]["role"] == "user":
    with st.spinner("🧠 WatkiBot is thinking..."):
        reply = send_message(st.session_state.selected_case, case_data["messages"][-1]["content"])
        case_data["messages"].append({"role": "assistant", "content": reply})
        st.rerun()
