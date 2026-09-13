import streamlit as st
from groq import Groq

st.set_page_config(page_title="AI Manager - @anyme", page_icon="🎬")

st.title("🎬 AI Manager for @anyme")
st.write("Ek task do, ye khud decide karega kaunsa kaam hai aur AI se result nikaal dega.")

# ---- API KEY ----
api_key = st.text_input("Apni Groq API Key yahan paste karo", type="password")

# ---- TASK ROUTING LOGIC ----
def classify_task(task_text):
    text = task_text.lower()
    if any(word in text for word in ["character", "art", "design", "look like", "image", "visual"]):
        return "art_prompt"
    elif any(word in text for word in ["dialogue", "conversation", "line", "say"]):
        return "dialogue"
    elif any(word in text for word in ["voice", "narration", "speak", "tone"]):
        return "voiceover"
    else:
        return "story"

SYSTEM_PROMPTS = {
    "story": "You are a creative anime story writer. Write an original, engaging story/scene idea based on the user's request. Never copy existing anime plots.",
    "dialogue": "You are a dialogue writer for anime characters. Write natural, emotional, anime-style dialogue for the scene the user describes.",
    "art_prompt": "You are an expert at writing image-generation prompts. Convert the user's description into a detailed anime-style character/scene prompt suitable for tools like Leonardo AI or Bing Image Creator.",
    "voiceover": "You rewrite scripts into natural, spoken, voiceover-friendly tone for text-to-speech tools like ElevenLabs.",
}

def run_task(task_text, api_key):
    category = classify_task(task_text)
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPTS[category]},
            {"role": "user", "content": task_text},
        ],
    )
    return category, response.choices[0].message.content

# ---- UI ----
task = st.text_area("Apna task likho (jaise: 'ek scene banao jahan hero pehli baar apni power discover karta hai')")

if st.button("Kaam Karwao"):
    if not api_key:
        st.error("Pehle apni free Groq API key daalo (neeche instructions hain).")
    elif not task:
        st.error("Task likho pehle.")
    else:
        with st.spinner("Manager kaam kar raha hai..."):
            category, result = run_task(task, api_key)
        st.success(f"Task type detect hua: **{category}**")
        st.write(result)

st.divider()
st.subheader("Free Groq API Key kaise banayen:")
st.markdown("""
1. [console.groq.com](https://console.groq.com) par jao
2. Free account banao (sirf email se)
3. Left menu se **API Keys** par jao → **Create API Key**
4. Wo key copy karke upar wale box mein paste karo
""")
