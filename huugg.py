from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from huggingface_hub import InferenceClient
from gtts import gTTS
import base64
import shutil
import os
import requests
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Hugging Face Inference Client
client = InferenceClient("meta-llama/Llama-3.2-11B-Vision-Instruct")

# Temporary audio file path
TEMP_AUDIO_FILE = "audio_temp.mp3"

@app.post("/describe-image/")
async def describe_image(file: UploadFile = File(...)):
    # Check file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only JPEG or PNG files are supported.")

    try:
        # Save the uploaded file temporarily
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Encode the image in base64
        with open(temp_file_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{base64_image}"

        # Send the image to the inference model
        custom_prompt = """
        You are a helpful assistant for a blind person, describing their surroundings as if you are with them in real-time.
        Your task is to provide clear and concise descriptions of what is currently in front of them.
        Focus on the most relevant objects, people, and any significant details that might help them understand their environment.

        Keep the description simple and direct.
        Prioritize information about:

        Primary objects present
        People, if any (describe their general appearance and actions)
        Text, if any (read it aloud if legible)
        Actions, if any (what is happening in the scene?)
        Environment (indoor, outdoor, nature, urban?)
        Important colors or visual details that stand out
        Avoid technical terms or unnecessary complexity. If the scene is unclear, explain that you cannot interpret it. Also, keep the responses short.
        """

        output = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                        {
                            "type": "text",
                            "text": custom_prompt,
                        },
                    ],
                },
            ],
        )

        # Extract the description
        description = output.choices[0].message.content.strip()

        # Generate text-to-speech audio
        tts = gTTS(text=description, lang='en', slow=False)
        tts.save(TEMP_AUDIO_FILE)

        # Clean up temporary image file
        os.remove(temp_file_path)

        # Return description and audio URL
        audio_url = "/get-audio"
        return JSONResponse(content={"description": description, "audio_url": audio_url})

    except Exception as e:
        # Handle errors
        raise HTTPException(status_code=500, detail=f"Error processing the image: {str(e)}")


@app.get("/get-audio/")
async def get_audio():
    try:
        if os.path.exists(TEMP_AUDIO_FILE):
            return FileResponse(TEMP_AUDIO_FILE, media_type="audio/mpeg", filename="description.mp3")
        else:
            raise HTTPException(status_code=404, detail="Audio file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@app.get("/describe-ip-camera/")
async def describe_ip_camera():
    try:
        # URL of the IP camera image
        ip_camera_url = "http://172.30.26.174/cam-hi.jpg"

        # Fetch the image from the IP camera
        response = requests.get(ip_camera_url, stream=True)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Unable to fetch image from the IP camera.")

        # Save the fetched image temporarily
        temp_file_path = "temp_ip_camera_image.jpg"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(response.raw, buffer)

        # Encode the image in base64
        with open(temp_file_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{base64_image}"

        # Send the image to the inference model
        custom_prompt = """
        You are a helpful assistant for a blind person, describing their surroundings as if you are with them in real-time.
        Your task is to provide clear and concise descriptions of what is currently in front of them.
        Focus on the most relevant objects, people, and any significant details that might help them understand their environment.

        Keep the description simple and direct.
        Prioritize information about:

        Primary objects present
        People, if any (describe their general appearance and actions)
        Text, if any (read it aloud if legible)
        Actions, if any (what is happening in the scene?)
        Environment (indoor, outdoor, nature, urban?)
        Important colors or visual details that stand out
        Avoid technical terms or unnecessary complexity. If the scene is unclear, explain that you cannot interpret it. Also, keep the responses short and also donto start with - In this image since you are describing a scene also make the response such that it could be converted to a audio such that a person is aying  so avoid markdown and new line characeters and bullets, .
        """

        output = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                        {
                            "type": "text",
                            "text": custom_prompt,
                        },
                    ],
                },
            ],
        )

        # Extract the description
        description = output.choices[0].message.content.strip()

        # Generate text-to-speech audio
        tts = gTTS(text=description, lang='en', slow=False)
        tts.save(TEMP_AUDIO_FILE)

        # Clean up temporary image file
        os.remove(temp_file_path)

        # Return description and audio URL
        audio_url = "/get-audio"
        return JSONResponse(content={"description": description, "audio_url": audio_url})

    except Exception as e:
        # Handle errors
        raise HTTPException(status_code=500, detail=f"Error processing the IP camera image: {str(e)}")


# Run the app using the following command:
# uvicorn script_name:app --reload
