from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, storage
import os
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *

app = Flask(__name__)
CORS(app)

# Firebase configuration
PROJECT_ID = os.environ.get('PROJECT_ID')
PRIVATE_KEY_ID = os.environ.get('PRIVATE_KEY_ID')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY').replace('\\n', '\n')
CLIENT_EMAIL = os.environ.get('CLIENT_EMAIL')
CLIENT_ID = os.environ.get('CLIENT_ID')
AUTH_URI = os.environ.get('AUTH_URI')
TOKEN_URI = os.environ.get('TOKEN_URI')
AUTH_PROVIDER_CERT_URL = os.environ.get('AUTH_PROVIDER_CERT_URL')
CLIENT_CERT_URL = os.environ.get('CLIENT_CERT_URL')
ELEVEN_API_KEY=os.environ.get('ELEVEN_API_KEY')

cred = credentials.Certificate({
    "type": "service_account",
    "project_id": PROJECT_ID,
    "private_key_id": PRIVATE_KEY_ID,
    "private_key": PRIVATE_KEY,
    "client_email": CLIENT_EMAIL,
    "client_id": CLIENT_ID,
    "auth_uri": AUTH_URI,
    "token_uri": TOKEN_URI,
    "auth_provider_x509_cert_url": AUTH_PROVIDER_CERT_URL,
    "client_x509_cert_url": CLIENT_CERT_URL
})

firebase_admin.initialize_app(
    cred, {'storageBucket': 'storyboard-739ee.appspot.com'})

def upload_to_firebase(file_name):
    bucket = storage.bucket()
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_name)
    blob.make_public()
    return blob.public_url

def split_text_into_lines(text, font, max_width):
    lines = []
    current_line = ""
    words = text.split()
    
    for word in words:
        test_line = current_line + word.upper() + " "  # Convert to uppercase here
        test_size = font.getlength(test_line)
        
        if test_size <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word.upper() + " "  # Convert to uppercase here
    
    if current_line:
        lines.append(current_line.strip())
    
    return lines

font_style = "laCartoonerie.TTF"
font_size = 20
max_width = 1040
line_spacing = 10
margin = {'top': 20, 'right': 20, 'bottom': 10, 'left': 20}

def create_image_with_text(text, font_path, font_size, max_width, line_spacing, margin):
    # Load the font
    font = ImageFont.truetype(font_path, font_size)
    
    # Calculate image size based on max width and text height
    lines = split_text_into_lines(text, font, max_width - margin['left'] - margin['right'])
    test_bbox = font.getbbox(lines[0])
    test_hsize = test_bbox[3] - test_bbox[1] 
    text_height = len(lines) * (test_hsize + line_spacing)
    
    image_width = max_width
    image_height = text_height + margin['top'] + margin['bottom']
    
    # Create a new image with a white background
    image = Image.new('RGB', (image_width, image_height), 'black')
    boarder = Image.new('RGB', (image_width - 10, image_height - 10), 'white')
    image.paste(boarder, (5, 5))
    draw = ImageDraw.Draw(image)
    
    # Start drawing text with the specified margins and line spacing
    y_position = margin['top']
    
    for line in lines:
        draw.text((margin['left'], y_position), line, fill='black', font=font)
        test_cbox = font.getbbox(line)
        test_chsize = test_cbox[3] - test_cbox[1]
        y_position += test_chsize + line_spacing
    
    return image



def change_Image(description, input_path):
    image = create_image_with_text(description, font_style, font_size, 1024, line_spacing, margin)
    image.save("output_image.png")
    image1 = Image.open(input_path)
    image2 = Image.open('output_image.png')
    original_width, original_height = image1.size
    merged_image = Image.new("RGB", (original_width, original_height))
    merged_image.paste(image1, (0, 0))
    y_offset = original_height - image2.height
    merged_image.paste(image2, (0, y_offset))
    merged_image.save("merged_image.jpg")

@app.route('/generate_video', methods=['POST'])
def generate_video():
    image_urls = request.json.get('image_urls').split('#')
    image_descriptions = request.json.get('image_descriptions').split('#')
    voice_id_name = request.json.get('voice_id_name')
    if voice_id_name=="Bella":
        voice_id="EXAVITQu4vr4xnSDxMaL"
    if voice_id_name=="Elli":
        voice_id="MF3mGyEYCl7XYWbV9V6O"
    if voice_id_name=="Emily":
        voice_id="LcfcDJNUP1GQjkzn1xUU"
    if voice_id_name=="Grace":
        voice_id="oWAxZDx7w5VEj9dCyTzz"
    if voice_id_name=="Josh":
        voice_id="TxGEqnHWrfWFTfGW9XjX"
    if voice_id_name=="Daniel":
        voice_id="onwK4e9ZLuTAKqWW03F9"
    if voice_id_name=="Dave":
        voice_id="CYw3kZ02Hs0563khs1Fj"
    if voice_id_name=="Dorothy":
        voice_id="ThT5KcBeYPX3keUQqHPh"
    if voice_id_name=="Joseph":
        voice_id="Zlb1dXrM653N07WRdFW3"
    if voice_id_name=="Matthew":
        voice_id="Yko7PKHZNXotIFUBG7I9"
    
    if len(image_urls) != len(image_descriptions):
        return jsonify({"error": "The number of images does not match the number of descriptions."}), 400
    
    clips = []

    for i, (img_url, description) in enumerate(zip(image_urls, image_descriptions)):
        # Download the image
        img_response = requests.get(img_url)
        input_path = f"image_{i}.png"
        
        with open(input_path, 'wb') as f:
            f.write(img_response.content)
        change_Image(description, input_path)
        img_path="merged_image.jpg"

        # Fetch audio from API for the description
        audio_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": "25eba609d073a7be50ab5162f846ccf1"
        }
        data = {
            "text": description,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        

        audio_response = requests.post(audio_url, json=data, headers=headers)
        audio_path = f"audio_{i}.mp3"
        with open(audio_path, 'wb') as f:
            f.write(audio_response.content)
        
        # Create clip with image and audio
        audio = AudioFileClip(audio_path)
        img_clip_with_audio = ImageClip(img_path, duration=audio.duration).set_audio(audio)
    
        clips.append(img_clip_with_audio)

    # Concatenate all clips and save the final video
    final_video = concatenate_videoclips(clips, method="compose")
    final_video_path = f"output_{int(time.time())}.mp4"
    final_video.write_videofile(final_video_path, fps=24, audio_codec='aac')

    video_url = upload_to_firebase(final_video_path)
    
    return jsonify({"video_url": video_url})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')