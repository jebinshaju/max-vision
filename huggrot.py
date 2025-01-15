from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from huggingface_hub import InferenceClient
from gtts import gTTS
import os
import requests
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import base64
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

# Temporary file paths
TEMP_IMAGE_FILE = "temp_ip_camera_image.jpg"
TEMP_AUDIO_FILE = "audio_temp.mp3"

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
        with open(TEMP_IMAGE_FILE, "wb") as buffer:
            buffer.write(response.content)

        # Optionally rotate the image
        with Image.open(TEMP_IMAGE_FILE) as img:
            rotated_img = img.rotate(270, expand=True)  # Rotate by 90 degrees
            rotated_img.save(TEMP_IMAGE_FILE)

        # Encode the rotated image in base64
        with open(TEMP_IMAGE_FILE, "rb") as f:
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
        Avoid technical terms or unnecessary complexity. If the scene is unclear then explain this as it might be a school or college settings with peoeple infront of you -  in minium words . Also, keep the responses short. Donot hallucinate 
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
        os.remove(TEMP_IMAGE_FILE)

        # Return description and audio URL
        audio_url = "/get-audio"
        return JSONResponse(content={"description": description, "audio_url": audio_url})

    except Exception as e:
        # Handle errors
        raise HTTPException(status_code=500, detail=f"Error processing the IP camera image: {str(e)}")


@app.get("/get-audio/")
async def get_audio():
    try:
        if os.path.exists(TEMP_AUDIO_FILE):
            return FileResponse(TEMP_AUDIO_FILE, media_type="audio/mpeg", filename="description.mp3")
        else:
            raise HTTPException(status_code=404, detail="Audio file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


# Run the app using the following command:
# uvicorn script_name:app --reload
