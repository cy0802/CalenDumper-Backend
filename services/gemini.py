import os
import time
import hashlib

import google.generativeai as genai

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

from services.model_setting import *
from models import Note, Dump

# API Key for genai
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

PROJECT_ID = "geminidiary"  # @param {type:"string"}
LOCATION = "us-central1" # @param {type:"string"}
vertexai.init(project=PROJECT_ID, location=LOCATION)

def generate(userId="111"):
    # Step 0: 從 database 取得文字和圖片 filter by user_id 文字不為空
    contents = Note.query.filter(Note.user_id == userId, Note.text != None).all()
    images = Note.query.filter(Note.user_id == userId, Note.picture != None).all()

    # Step 1: 使用 text 模型生成中文 dump-prompt 和建議
    model = genai.GenerativeModel(model_name="gemini-1.5-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

    text_prompts = ''.join([f"""### 事件：{content.event_summary}\n
                            ### 心得：{content.text}\n""" for content in contents])
    image_prompts = [genai.upload_file(path=image.picture, display_name=image.picture.strip(".py"))
                for image in images]

    prompt_parts = [
        system_message,
        text_prompts,
        *image_prompts,
    ]
    print(text_prompts)
    print(image_prompts)
    response = model.generate_content(prompt_parts)

    # Step 2: 提取生成的中文總結和 dump-prompt
    print(response.text)
    try:
      photo_dump = response.text.split("##")[1]
    except:
      photo_dump = response.text
    try:
      summarize = response.text.split("##")[2]
    except:
      summarize = response.text

    print(photo_dump)
    print()
    print(summarize)

    # Step 3: 將中文 dump-prompt 翻譯成英文
    translate_model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                              generation_config=generation_config,
                              safety_settings=safety_settings)
    translation_response = translate_model.generate_content([translate_system_message, photo_dump])
    dump_prompt = translation_response.text

    # Step 4: 使用 image 模型生成圖片
    imagen_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
    
    # 生成圖片
    dump_response = imagen_model.generate_images(
      prompt=dump_prompt,
    )
    
    # Step 5: 將圖片和總結返回前端
    dump_image = dump_response.images[0]
    hash_value = hashlib.sha256(f"{userId}_{time.time()}".encode('utf-8')).hexdigest()
    dump_image_path = dump_image.save(f"./{hash_value}")
    Dump(user_id=userId, picture=dump_image_path, text=summarize).save()

    print("Dump image saved successfully.")

    # 將總結和圖片一起返回給前端
    return {'summary': summarize, 'image_url': dump_image_path}