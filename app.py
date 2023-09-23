import streamlit as st
import threading
from queue import Queue
import os
from youtube_transcript_api import YouTubeTranscriptApi
import os
import instadown
import time
from pytube import YouTube
from moviepy.editor import VideoFileClip
import sqlite3
from youtube_transcript_api import YouTubeTranscriptApi
import re
import hydralit_components as hc
import hashlib
import streamlit.components.v1 as components

# Initialize SQLite database for user accounts and download history
conn = sqlite3.connect('youtube_downloader.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS downloads
             (id INTEGER PRIMARY KEY, user_id INTEGER, url TEXT, type TEXT, date TEXT)''')

# Make it look nice from the start
st.set_page_config(layout='wide', initial_sidebar_state='collapsed') #do not touch it here
# home_name='Home', login_name='Login', 
# Define the primary menu definition with CSS classes for icons
menu_data = [
    {'icon': "fas fa-house", 'label': "Home"},
    {'icon': "fab fa-youtube", 'label': "Yt Downloader"},
    {'icon': "fab fa-youtube",'id': 'Yt Converter', 'label': "Yt Converter"},
    {'icon': "fab fa-youtube",'id': 'Yt to MP3','label': "Yt to MP3"},
    {'icon': "fab fa-youtube",'id': "Transcript", 'label': "Yt Subs Downloader"},
]

# Create a navigation bar using hydralit_components
menu_id = hc.nav_bar(menu_definition=menu_data, sticky_mode='pinned', sticky_nav=True, hide_streamlit_markers=False, override_theme={'txc_inactive': '#FFFFFF'})

# Helper function for audio download
def download_audio(youtube_url, download_format):
    st.info("Downloading audio...")
    try:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()

        if not stream:
            st.warning("No suitable audio format available for this video.")
            return

        output_path = os.path.join("downloads", f"{yt.title}.mp3")
        stream.download(output_path=output_path)
        st.success(f"Downloaded audio: {yt.title}.mp3")
    except Exception as e:
        st.error(f"Error: {e}")
# Function to extract video ID from YouTube URL
def extract_video_id(youtube_url):
    try:
        if "youtu.be" in youtube_url:
            video_id = youtube_url.split("/")[-1]
        elif "youtube.com" in youtube_url:
            video_id = youtube_url.split("v=")[-1].split("&")[0]
        else:
            video_id = None
        return video_id
    except Exception:
        return None

# Helper function for video download it is for convertor page download
def download_video(youtube_url, output_format, output_path):
    st.info("Downloading video...")
    try:
        yt = YouTube(youtube_url)
        if yt is None:
            st.error("Failed to fetch the YouTube video. Please check the URL.")
            return None

        stream = yt.streams.filter(res=output_format).first()
        if stream is None:
            st.error("No suitable video format available for this video.")
            return None

        stream.download(output_path=output_path)
        st.success(f"Downloaded video: {yt.title}")
        return yt.title, output_path
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None
# Helper function for video conversion
def convert_video(input_path, output_format):
    st.info("Converting video...")
    try:
        video = VideoFileClip(input_path)
        output_path = os.path.splitext(input_path)[0] + f".{output_format}"
        video.write_videofile(output_path, codec=output_format)
        st.success(f"Video converted to {output_format}: {output_path}")
        return output_path
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Function to download the transcript even if it's disabled
def download_transcript(youtube_url):
    try:
        video_id = extract_video_id(youtube_url)
        if video_id:
            st.info("Fetching transcript...")
            # Fetch the transcript using youtube_transcript_api
            transcript = YouTubeTranscriptApi.get_transcript(video_id)

            if transcript:
                # Convert transcript to SRT format
                srt_transcript = ""
                for i, entry in enumerate(transcript, start=1):
                    srt_transcript += f"{i}\n{entry['start']} --> {entry['start']}\n{entry['text']}\n\n"

                # Save the transcript as an SRT file
                video_title = clean_filename(video_id)
                output_path = os.path.join("downloads", f"{video_title}.srt")
                with open(output_path, 'w', encoding='utf-8') as file:
                    file.write(srt_transcript)

                st.success(f"Downloaded transcript: {video_title}.srt")
            else:
                st.warning("No transcript available for this video.")
        else:
            st.error("Invalid YouTube video URL. Please provide a valid URL.")
    except Exception as e:
        st.error(f"Error: {e}")

# Function to clean up video title for use in filenames
def clean_filename(filename):
    # Remove any characters that are not alphanumeric or spaces
    cleaned_filename = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    cleaned_filename = cleaned_filename.replace(' ', '_')
    return cleaned_filename
# Create Streamlit pages for each downloader
if menu_id == 'Yt Downloader':
    # Streamlit page for YouTube video downloader
    st.header("Yt Video Downloader")
    youtube_url = st.text_input("Enter YouTube Video URL:")
    download_format = st.selectbox("Select Video Quality:", ["144p","240p", "360p","480p", "1080p"])
    download_option = st.selectbox("Select Format:", ["Video", "Audio", "Transcript"])

    if st.button("Download"):
        st.info("Downloading...")
        try:
            yt = YouTube(youtube_url)

            if download_option == "Video":
                stream = yt.streams.filter(res=download_format).first()
                video_title = clean_filename(yt.title)
                output_path = os.path.join("downloads", f"{video_title}.mp4")
                stream.download(output_path=output_path)
                st.success(f"Downloaded video: {video_title}")
            elif download_option == "Audio":
                download_audio(youtube_url, download_option)
            elif download_option == "Transcript":
                download_transcript(youtube_url)
        except Exception as e:
            st.error(f"Error: {e}")

# Yt to MP3 Page
if menu_id == 'Yt to MP3':
    st.header("Yt to MP3 Downloader")
    youtube_url = st.text_input("Enter YouTube Video URL:")
    if st.button("Download MP3"):
        download_audio(youtube_url, "mp3")
# Yt Converter Page
# Yt Converter Page
if menu_id == 'Yt Converter':
    st.header("Yt Video Converter")
    conversion_option = st.radio("Choose a conversion option:", ["Upload a video file", "Provide a YouTube URL"])
    if conversion_option == "Upload a video file":
        uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "AVI", "MKV", "MOV", "WEBM"])
        if uploaded_file is not None:
            with open("uploads/uploaded_video.mp4", "webm") as f:
                f.write(uploaded_file.read())
                st.success(f"Uploaded video file: {uploaded_file.name}")
                mp4_path = "uploads/uploaded_video.mp4"
                AVI_path = "uploads/uploaded_video.AVI"
                MKV_path = "uploads/uploaded_video.MKV"
                MOV_path = "uploads/uploaded_video.MOV"
                WEBM_path = "uploads/uploaded_video.WEBM"
                output_formats = st.multiselect("Select Output Formats:", ["MP4", "AVI", "MKV", "MOV", "WEBM"])

    elif conversion_option == "Provide a YouTube URL":
        youtube_url = st.text_input("Enter YouTube Video URL:")

    output_formats = st.multiselect("Select Output Formats:", ["MP4", "AVI", "MKV", "MOV", "WEBM"])

    if st.button("Convert Video"):
        st.info("Converting video...")
        try:
            if conversion_option == "Provide a YouTube URL":
                yt_title, mp4_path = download_video(youtube_url, download_format, "downloads")
                if yt_title is not None and mp4_path is not None:
                   for output_format in output_formats:
                    convert_path = convert_video(mp4_path, output_format.lower())
                    if convert_path is not None:
                        st.success(f"Video converted to {output_format}: {convert_path}")
        except Exception as e:
            st.error(f"Error: {e}")

# Yt Subs Downloader Page
if menu_id == 'Transcript':
    st.header("Yt Subtitles Downloader")
    youtube_url = st.text_input("Enter YouTube Video URL:")
    if st.button("Download Subtitles"):
        st.info("Downloading subtitles...")
        download_transcript(youtube_url)

# Create Streamlit pages for each menu item
if menu_id == 'Home':
    # Set padding, font, and background color
    padding = 2
    bg_color = "#0E1117"
    st.write(
        f'<style> .reportview-container .main .block-container{{padding-top: {padding}rem; padding-right: {padding}rem; padding-left: {padding}rem; padding-bottom: {padding}rem; background-color: {bg_color}; font-family: "Poppins", sans-serif;}} </style>',
        unsafe_allow_html=True)

    # Center and style the header
    st.markdown('<h1 style="text-align:center; font-size: 3em; font-weight:bold;">YouTube Download and Converter</h1>',
                unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; font-size:1.5rem;">Download videos, convert formats, extract audio and subtitles</p>',
                unsafe_allow_html=True)

    st.header("")  # Blank header for spacing

    # Create columns for image and content
    col1, col2 = st.columns([1, 2])

    with col1:
        # Add an emoji or icon
        st.markdown("<h1>📼</h1>", unsafe_allow_html=True)

    with col2:
        # Add content
        st.write("""
        <h2>Ytdownloader Instructions</h2>
        <ol>
            <li>Search by name or directly paste the link of the video you want to convert</li>
            <li>Click "Start" button to begin the converting process</li>
            <li>Select the audio(mp3)/video(mp4) format you want to download, then click "Download" button</li>
        </ol>

        <h2>Ytdownloader Features</h2>
        <ul>
            <li>Unlimited downloads and always free</li>
            <li>High-speed YouTube video converter</li>
            <li>Free YouTube Video Downloader & No registration required</li>
            <li>Support downloading with all formats</li>
        </ul>

        <h2>Free downloader Online</h2>
        <ul>
            <li>Unlimited conversion and free download.</li>
            <li>Mp3(Audio) & Mp4(Video) converter</li>
            <li>Directly Download Video & Music without restrictions and always for free.</li>
            <li>Easy Download Fully compatible with all browsers.</li>
        </ul>
        """, unsafe_allow_html=True)

    st.markdown("---")  # Horizontal rule
# Stylish footer with app name, menu links, and copyright section
footer = st.empty()

# Stylish footer
footer.markdown(
    """
    <style>
        .footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #FFFFFF;
            padding: 1rem;
            box-shadow: 0px -2px 10px 0px rgba(0,0,0,0.2);
        }
        .app-name {
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }
        .menu-links {
            font-size: 16px;
        }
        .menu-links a {
            text-decoration: none;
            color: #333;
            margin-right: 20px;
        }
        .menu-links a:hover {
            color: #FF6F61;
        }
        .copyright {
            font-size: 14px;
            color: #777;
        }
    </style>
    """
, unsafe_allow_html=True)

# Footer content
footer.markdown(
    """
    <div class="footer">
        <div class="app-name">
            Yt Downloader
        </div>
        <div class="menu-links">
            <a href="/Yt Downloader">Yt Downloader</a>
            <a href="/About Us">About Us</a>
            <a href="/FAQs">FAQs</a>
            <a href="/Contact Us">Contact Us</a>
            <a href="/Terms of Service">Terms of Service</a>
            <a href="/Privacy Policy">Privacy Policy</a>
        </div>
        <div class="copyright">
            &copy; 2023 All Rights Reserved.
        </div>
    </div>
    """
, unsafe_allow_html=True)

    
# Main app
def main():
 # Initialize 'user_id' in st.session_state if it doesn't exist
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
# Home page
def home():
    st.header("Home")
    st.subheader("Download YouTube Video")
    download_url = st.text_input("Enter YouTube URL:")
    
    if download_url:
        st.subheader("Video Format Selection")
        download_format = st.selectbox("Select Video Format:", ["144p", "360p", "480p", "720p", "1080p", "4k"])
        
        st.subheader("Video Download Options")
        output_path = st.text_input("Save the video as (include file extension, e.g., video.mp4):")
        
        if st.button("Download Video"):
            download_video(download_url, download_format, output_path)

# Threading for the download queue processing
def process_queue():
    while not download_queue.empty():
        download = download_queue.get()
        if download["type"] == "video":
            download_video(download["url"], download["format"])
        elif download["type"] == "audio":
            download_audio(download["url"])

# Helper function for video download
def download_video(url, download_format, output_path):
    st.info("Downloading video...")
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(res=download_format).first()
        stream.download(output_path=output_path)
        record_download(url, "video")
        st.success(f"Downloaded video: {yt.title}")
    except Exception as e:
        st.error(f"Error: {e}")

# Record download in database
def record_download(url, download_type):
    date = time.strftime("%Y-%m-%d")
    c.execute("INSERT INTO downloads (user_id, url, type, date) VALUES (?, ?, ?, ?)",
              (st.session_state.user_id, url, download_type, date))
    conn.commit()

def submit_feedback():
    st.header("Submit Feedback")
    feedback = st.text_area("Your Feedback:")
    
    if st.button("Submit Feedback"):
        # Implement logic to send feedback to developer 
        st.success("Feedback submitted successfully.")

if __name__ == "__main__":
    main()
