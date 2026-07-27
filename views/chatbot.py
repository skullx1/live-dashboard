import anthropic
import streamlit as st

def show():
    st.markdown('<div class="dash-title">💬 Stock <span>Assistant</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-caption">Ask questions about market indicators, technical terms, or trading concepts.</div>', unsafe_allow_html=True)

    anthropic_key = st.secrets.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        st.error("ANTHROPIC_API_KEY was not found in secrets.toml.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask any financial or stock market question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client = anthropic.Anthropic(api_key=anthropic_key)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = client.messages.create(
                        model="claude-sonnet-5",
                        max_tokens=600,
                        system="You are a helpful educational financial assistant. Explain financial concepts clearly without giving personalized financial or trading advice.",
                        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    )
                except anthropic.NotFoundError:
                    response = client.messages.create(
                        model="claude-haiku-4-5",
                        max_tokens=600,
                        system="You are a helpful educational financial assistant. Explain financial concepts clearly without giving personalized financial or trading advice.",
                        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    )

                bot_reply = response.content[0].text
                st.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})