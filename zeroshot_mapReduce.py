import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.chains.combine_documents.base import Document
import os
from langchain.text_splitter import CharacterTextSplitter
from datetime import datetime
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

# OpenAI APIキーを設定
os.environ["OPENAI_API_KEY"] = 'ここにAPIキーを入力'

def init_page():
    st.set_page_config(
        page_title="要約アプリ",
        page_icon="🧠"
    )
    st.header("要約アプリ 🧠")
    
    # サイドバーのタイトルを表示
    st.sidebar.title("モデル選択")
    st.session_state.costs = []

def init_messages():
    # サイドバーにボタンを設置
    clear_button = st.sidebar.button("履歴削除", key="clear")
    if clear_button or "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content="")
        ]
        st.session_state.costs = []

def select_model():
    model = st.sidebar.radio("Choose a model:", ("GPT-3.5", "GPT-4"))
    if model == "GPT-3.5":
        model_name = "gpt-3.5-turbo"
    else:
        model_name = "gpt-4"

    return ChatOpenAI(temperature=0, model_name=model_name)

def get_text_input():
    text_input = st.text_area("テキストを入力してください:", key="input", height=200)
    text_splitter = CharacterTextSplitter(separator="。", chunk_size=200)
    texts = text_splitter.split_text(text_input)
    return texts

def summarize(llm, docs):
    prompt_template = """
    入力する文章を要約してください。
    #入力する文章
    {text:}
    #出力形式
    要約した文章:
    """

    prompt_map = """
    入力する文章を要約してください。
    #入力する文章
    {text:}
    #出力形式
    要約した文章:
    """

    PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])
    prompt_map = PromptTemplate(template=prompt_map, input_variables=["text"])

    with get_openai_callback() as cb:
        chain = load_summarize_chain( 
            llm,
            chain_type="map_reduce",
            map_prompt=PROMPT,
            combine_prompt = prompt_map,
            collapse_prompt=prompt_map,
            verbose=True
        )

        # Create a Document with page_content set to content
        document = docs
        response = chain({"input_documents": docs}, return_only_outputs=True)
        
    return response['output_text'], cb.total_cost

def main():
    init_page()
    llm = select_model()
    init_messages()

    container = st.container()
    response_container = st.container()

    with container:
        text_input = get_text_input()
        run_button = st.button("実行")
    start_time = None
    if text_input and run_button:
        document = [Document(page_content=t) for t in text_input]

        with st.spinner("ChatGPT is typing ..."):
            start_time = datetime.now()
            output_text, cost = summarize(llm, document)
        st.session_state.costs.append(cost)
    else:
        output_text = None

    if output_text:
        with response_container:
            st.markdown("## 要約された文章")
            st.write(text_input)
            st.markdown("## 要約された文章")
            st.write(output_text)

    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds() if start_time else None
    if execution_time:
        st.sidebar.markdown(f"**実行時間: {execution_time:.2f}秒**")
    costs = st.session_state.get('costs', [])
    st.sidebar.markdown("## Costs")
    st.sidebar.markdown(f"**Total cost: ${sum(costs):.5f}**")
    for cost in costs:
        st.sidebar.markdown(f"- ${cost:.5f}")

if __name__ == '__main__':
    main()