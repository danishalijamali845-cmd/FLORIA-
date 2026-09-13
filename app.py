import streamlit as st
import urllib.parse
import requests
import io
import os
import re
import json
import tempfile
from groq import Groq
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip

st.set_page_config(page_title="AI Manager - @anyme", page_icon="🎬")

st.title("🎬 AI Manager for @anyme")
st.write("Apni poori episode script paste karo — app khud scenes plan karega, images banayega, English voiceover bolega, captions lagayega, aur poori video jod kar dega.")

api_key = st.text_input("Apni Groq API Key yahan paste karo", type="password")
script_text = st.text_area("Poori episode script yahan paste karo", height=250)
seconds_per_scene = st.slider("Har scene image kitni der dikhe (seconds)", 15, 60, 30)

st.caption("Note: 20-minute video mein bohot saari images/audio banti hain, isliye ye process 20-40 minute tak le sakta hai. Sabar se wait karna.")

def split_into_chunks(text, seconds_per_scene, words_per_second=2.2):
    words = text.split()
    words_per_chunk = max(8, int(seconds_per_scene * words_per_second))
    chunks = [" ".join(words[i:i + words_per_chunk]) for i in range(0, len(words), words_per_chunk)]
    return [c for c in chunks if c.strip()]

def get_image_prompts(chunks, api_key):
    client = Groq(api_key=api_key)
    numbered = "\n".join([f"{i+1}. {c}" for i, c in enumerate(chunks)])
    system = (
        "For each numbered script segment below, write ONE short (max 20 words) anime-style visual "
        "image description matching that segment's content. Reply with ONLY a valid JSON array of strings, "
        "in the same order, no extra text. Example: [\"prompt for 1\", \"prompt for 2\"]"
    )
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": numbered},
        ],
        max_tokens=min(6000, len(chunks) * 40 + 300),
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def download_image(prompt_text, save_path):
    encoded = urllib.parse.quote(prompt_text + ", anime style, high detail, cinematic")
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=576"
    r = requests.get(url, timeout=60)
    with open(save_path, "wb") as f:
        f.write(r.content)

def build_video(chunks, image_prompts, workdir, progress_bar):
    clips = []
    total = len(chunks)
    for i, (chunk_text, prompt) in enumerate(zip(chunks, image_prompts)):
        img_path = os.path.join(workdir, f"scene_{i}.jpg")
        audio_path = os.path.join(workdir, f"voice_{i}.mp3")

        download_image(prompt, img_path)
        gTTS(text=chunk_text, lang="en").save(audio_path)
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        img_clip = ImageClip(img_path).with_duration(duration).resized(lambda t: 1 + 0.03 * t)
        caption = TextClip(
            font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            text=chunk_text, font_size=28, color="white",
            method="caption", size=(950, None), stroke_color="black", stroke_width=1.5
        ).with_duration(duration).with_position(("center", "bottom"))

        scene = CompositeVideoClip([img_clip, caption]).with_audio(audio_clip)
        clips.append(scene)
        progress_bar.progress((i + 1) / total, text=f"Scene {i+1}/{total} taiyar")

    final = concatenate_videoclips(clips, method="compose")
    out_path = os.path.join(workdir, "final_video.mp4")
    final.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
    return out_path

if st.button("Full Video Banao"):
    if not api_key:
        st.error("Pehle apni free Groq API key daalo.")
    elif not script_text.strip():
        st.error("Pehle apni script paste karo.")
    else:
        try:
            chunks = split_into_chunks(script_text, seconds_per_scene)
            st.info(f"Script ko {len(chunks)} scenes mein split kiya gaya hai.")

            with st.spinner("Har scene ke liye image prompts ban rahe hain..."):
                image_prompts = get_image_prompts(chunks, api_key)

            with tempfile.TemporaryDirectory() as workdir:
                progress_bar = st.progress(0, text="Shuru ho raha hai...")
                video_path = build_video(chunks, image_prompts, workdir, progress_bar)
                with open(video_path, "rb") as f:
                    video_bytes = f.read()
                st.success("Video ban gayi!")
                st.video(video_bytes)
                st.download_button("Video Download Karo", video_bytes, file_name="anyme_episode.mp4")
        except Exception as e:
            st.error(f"Kuch masla hua: {e}")

st.divider()
st.subheader("Free Groq API Key kaise banayen:")
st.markdown("""
1. [console.groq.com](https://console.groq.com) par jao
2. Free account banao (sirf email se)
3. Left menu se **API Keys** par jao → **Create API Key**
4. Wo key copy karke upar wale box mein paste karo
""")
