from flask import Flask, render_template, request, redirect, url_for, flash
import os
from frame_extractor import extract_frames
from PIL import Image
from deep_translator import GoogleTranslator
from gtts import gTTS
import random  # Importing the random module
import string  # Importing the string module
import pytesseract

# Configure the path to Tesseract OCR executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Supported languages for translation and TTS
languages = {
    'en': 'English', 'ta': 'Tamil', 'hi': 'Hindi', 'es': 'Spanish', 'fr': 'French',
    'de': 'German', 'zh-cn': 'Chinese (Simplified)', 'ja': 'Japanese', 'ko': 'Korean',
    'it': 'Italian', 'ar': 'Arabic', 'pt': 'Portuguese', 'ru': 'Russian', 'bn': 'Bengali',
    'ur': 'Urdu', 'te': 'Telugu', 'ml': 'Malayalam'
}

@app.route('/')
def index():
    return render_template('index.html', languages=languages)

@app.route('/process', methods=['POST'])
def process():
    video_file = request.files['videoFile']
    output_dir = request.form['outputDir']
    skip_frames = int(request.form['frameInterval'])
    translate_lang = request.form['translateLang']
    audio_lang = request.form['audioLang']

    # Save video to the server
    video_path = os.path.join(output_dir, video_file.filename)
    video_file.save(video_path)

    # Extract frames from the video
    extract_frames(video_path, output_dir, skip_frames)

    # Redirect to frame selection
    return redirect(url_for('select_frame', output_dir=output_dir, translate_lang=translate_lang, audio_lang=audio_lang))

@app.route('/select_frame')
def select_frame():
    output_dir = request.args.get('output_dir')
    translate_lang = request.args.get('translate_lang')
    audio_lang = request.args.get('audio_lang')
    frames = [f for f in os.listdir(output_dir) if f.startswith('frame_') and f.endswith('.jpg')]
    return render_template('choose_frame.html', frames=frames, output_dir=output_dir, translate_lang=translate_lang, audio_lang=audio_lang)

@app.route('/process_frame', methods=['POST'])
def process_frame():
    frame_path = request.form['frame']
    output_dir = request.form['output_dir']
    translate_lang = request.form['translate_lang']
    audio_lang = request.form['audio_lang']

    # Perform OCR on the selected frame
    text = pytesseract.image_to_string(Image.open(frame_path))

    if not text.strip():
        flash("No text found in the selected frame. Please choose a different frame.")
        return redirect(url_for('select_frame', output_dir=output_dir, translate_lang=translate_lang, audio_lang=audio_lang))

    # Translate text
    translated_text = GoogleTranslator(source='auto', target=translate_lang).translate(text)

    if not translated_text.strip():
        flash("Translation yielded no text. Please try a different frame or text.")
        return redirect(url_for('select_frame', output_dir=output_dir, translate_lang=translate_lang, audio_lang=audio_lang))

    # Convert translated text to speech and save audio in the static folder
    audio_file = f"translated_audio_{''.join(random.choices(string.ascii_lowercase, k=5))}.mp3"
    audio_path = os.path.join('static', audio_file)
    speech = gTTS(text=translated_text, lang=audio_lang, slow=False)
    speech.save(audio_path)

    flash("Text extracted, translated, and audio generated successfully.")
    
    # Render the choose_frame.html page with the translated text and audio file
    return render_template('choose_frame.html', frames=[os.path.basename(frame_path)], output_dir=output_dir,
                           translate_lang=translate_lang, audio_lang=audio_lang, 
                           translated_text=translated_text, audio_file=audio_file)

if __name__ == '__main__':
    app.run(debug=True)
