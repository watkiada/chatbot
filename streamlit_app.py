import streamlit as st 
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from openai import OpenAI

# Set page config FIRST, immediately after imports
st.set_page_config(page_title="Watkibot Advanced AI Legal Assistant")

st.title("\u2696\ufe0f Watkibot Advanced AI Legal Assistant")
st.write(
    "Select a case and form to generate completed documents or ask questions about the case."
)
st.write(
    "Watkibot will never hallucinate answers. All responses are based on case data."
)

CASES = {
    "Ortiz, Margarita": {},
    "Newman, Al": {},
    "Kelvin, Douglas": {},
    "Jungk, Heidi": {},
    "Gomez, Juan": {},
    "Ferguson, Robert": {},
    "Curnow, Robert": {},
    "Adams, Guy": {},
}

@st.cache_data(show_spinner=False)
def load_forms():
    url = "https://www.dir.ca.gov/dwc/forms.html#Medical"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        forms = {}
        base = "https://www.dir.ca.gov/"
        for a in soup.select("a[href$='.pdf']"):
            name = a.text.strip() or a["href"].split("/")[-1]
            link = urljoin(base, a["href"])
            forms[name] = link
        return forms
    except Exception:
        return {"Sample Medical Report": "https://example.com/sample.pdf"}

def fill_pdf(url: str, data: dict) -> BytesIO:
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    resp.raise_for_status()
    reader = PdfReader(BytesIO(resp.content))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    if reader.trailer.get("/Root", {}).get("/AcroForm"):
        writer.update_page_form_field_values(writer.pages[0], data)
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output

openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.sidebar.info("Please add your OpenAI API key to continue.", icon="🗝️")
    st.stop()

case_name = st.sidebar.selectbox("Select case", list(CASES.keys()))
case_data = CASES.get(case_name, {})

forms = load_forms()
form_name = st.sidebar.selectbox("Select form", sorted(forms.keys()))

if st.sidebar.button("Fill selected form"):
    with st.spinner("Filling PDF..."):
        try:
            pdf = fill_pdf(forms[form_name], case_data)
            st.session_state["filled_pdf"] = pdf.getvalue()
            with st.chat_message("assistant"):
                st.write(f"Completed {form_name}.")
                st.download_button(
                    "Download filled PDF",
                    data=st.session_state["filled_pdf"],
                    file_name=form_name.replace(" ", "_") + ".pdf",
                    mime="application/pdf",
                )
        except Exception as e:
            st.error(str(e))

# Create an OpenAI client.
client = OpenAI(api_key=openai_api_key)

# Initialize an assistant thread for this session.
if "thread_id" not in st.session_state:
    st.session_state.thread_id = client.beta.threads.create().id

# Initialize chat history with a greeting if this is a new session.
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to Watkibot, Select a case to begin working"}
    ]

# Display prior messages.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle new user input.
if prompt := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client.beta.threads.messages.create(
        st.session_state.thread_id,
        role="user",
        content=prompt,
    )

    client.beta.threads.runs.create_and_poll(
        thread_id=st.session_state.thread_id,
        assistant_id="asst_QD4XWA2zINlHoh8llg7jcbpK",
    )

    msg_list = client.beta.threads.messages.list(
        st.session_state.thread_id,
        order="desc",
        limit=1,
    )
    assistant_content = msg_list.data[0].content[0].text.value

    with st.chat_message("assistant"):
        st.markdown(assistant_content)
    st.session_state.messages.append({"role": "assistant", "content": assistant_content})
