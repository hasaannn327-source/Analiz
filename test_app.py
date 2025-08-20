import streamlit as st

st.title("🧪 Test Uygulaması")
st.write("Bu basit bir test uygulamasıdır.")
st.success("✅ Streamlit çalışıyor!")

if st.button("Test Butonu"):
    st.balloons()
    st.write("🎉 Buton çalışıyor!")