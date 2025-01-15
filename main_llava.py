from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
import shutil
import ollama
from gtts import gTTS
import uuid
import os
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from pydub import AudioSegment
from google.cloud import storage
from fastapi.middleware.cors import CORSMiddleware

# Initialize Firebase Admin SDK
cred = credentials.Certificate("echosight-firebase-adminsdk-h0bdv-2738befc2a.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Google Cloud Storage client
storage_client = storage.Client.from_service_account_json("echosight-firebase-adminsdk-h0bdv-2738befc2a.json")
bucket_name = "echosight.firebasestorage.app"
bucket = storage_client.bucket(bucket_name)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom prompt for Ollama
custom_prompt = """
You are a helpful assistant for a blind person, describing their surroundings as if you are with them in real-time.
Your task is to provide clear and concise descriptions of what is currently in front of them.
Focus on the most relevant objects, people, and any significant details that might help them understand their environment.

Keep the description simple and direct.
Prioritize information about:
- Primary objects present
- People, if any (describe their general appearance and actions)
- Text, if any (read it aloud if legible)
- Actions, if any (what is happening in the scene?)
- Environment (indoor, outdoor, nature, urban?)
- Important colors or visual details that stand out
Avoid technical terms or unnecessary complexity. If the scene is unclear, explain that you cannot interpret it.
"""

# Helper: Text-to-Speech Conversion
def text_to_speech(text, voice_type="default"):
    try:
        tld = "co.uk" if voice_type == "good_person" else "com"
        audio_file = f"audio/audio_{uuid.uuid4()}.mp3"
        os.makedirs("audio", exist_ok=True)
        tts = gTTS(text=text, lang='en', tld=tld, slow=False)
        tts.save(audio_file)
        return audio_file
    except Exception as e:
        print(f"Error converting to speech: {e}")
        return None

# Helper: Generate description using Ollama
def generate_description(image_path):
    try:
        res = ollama.chat(
            model="llava",
            messages=[
                {
                    "role": "user",
                    "content": custom_prompt,
                    'images': [image_path]
                }
            ]
        )
        if 'message' in res:
            return res['message']['content']
        return "Description could not be generated."
    except Exception as e:
        print(f"Error generating description: {e}")
        return "Error in generating description."

# Endpoint: Process Image and Generate Description and Audio
@app.post("/process_image/")
async def process_image(file: UploadFile = File(...)):
    try:
        # Save uploaded image
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Generate description
        description = generate_description(temp_file_path)
        if not description:
            raise HTTPException(status_code=500, detail="Failed to generate description.")

        # Convert description to audio
        audio_file = text_to_speech(description)
        if not audio_file:
            raise HTTPException(status_code=500, detail="Failed to generate audio.")

        # Upload audio file to Firebase Storage
        blob = bucket.blob(os.path.basename(audio_file))
        blob.upload_from_filename(audio_file)
        blob.make_public()
        audio_url = blob.public_url

        # Save data to Firestore
        doc_ref = db.collection('image_descriptions').document(str(uuid.uuid4()))
        doc_ref.set({
            'description': description,
            'audio_url': audio_url,
            'timestamp': datetime.utcnow()
        })

        # Cleanup
        if os.path.exists(audio_file):
            os.remove(audio_file)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        return {"description": description, "audio_url": audio_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

# Endpoint: Generate Daily Summary and Podcast
# @app.get("/daily_summary/")
# async def daily_summary():
#     try:
#         today = datetime.utcnow().date()
#         start_of_day = datetime(today.year, today.month, today.day)
#         end_of_day = start_of_day + timedelta(days=1)

#         # Fetch today's entries
#         entries = db.collection('image_descriptions').where(
#             'timestamp', '>=', start_of_day).where('timestamp', '<', end_of_day).stream()

#         descriptions = []
#         for entry in entries:
#             data = entry.to_dict()
#             descriptions.append(data['description'])

#         if not descriptions:
#             return {"summary": "No entries found for today."}

#         combined_text = " ".join(descriptions)
#         diary_entry = f"Today, the following events occurred: {combined_text}"

#         # Generate audio podcast
#         podcast_audio_file = text_to_speech(diary_entry)
#         if not podcast_audio_file:
#             raise HTTPException(status_code=500, detail="Failed to generate podcast audio.")

#         # Upload podcast audio to Firebase Storage
#         blob = bucket.blob(os.path.basename(podcast_audio_file))
#         blob.upload_from_filename(podcast_audio_file)
#         blob.make_public()
#         podcast_url = blob.public_url

#         # Cleanup
#         if os.path.exists(podcast_audio_file):
#             os.remove(podcast_audio_file)

#         # Save summary to Firestore
#         doc_ref = db.collection('daily_diaries').document(today.isoformat())
#         doc_ref.set({
#             'summary': diary_entry,
#             'podcast_url': podcast_url,
#             'timestamp': datetime.utcnow()
#         })

#         return {"summary": diary_entry, "podcast_url": podcast_url}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

# # Endpoint: Fetch All Diaries with Pagination
# @app.get("/fetch_all_diaries/")
# async def fetch_all_diaries(page: int = 1, page_size: int = 10):
#     try:
#         diaries_ref = db.collection('daily_diaries').order_by('timestamp', direction=firestore.Query.DESCENDING)
#         all_diaries = list(diaries_ref.stream())
#         total_diaries = len(all_diaries)

#         # Paginate
#         skip = (page - 1) * page_size
#         paginated_diaries = all_diaries[skip:skip + page_size]

#         diaries = []
#         for diary in paginated_diaries:
#             data = diary.to_dict()
#             diaries.append({
#                 'summary': data['summary'],
#                 'podcast_url': data.get('podcast_url', ''),
#                 'timestamp': data['timestamp']
#             })

#         return {"total_diaries": total_diaries, "diaries": diaries}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
