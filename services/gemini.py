from flask import Flask, request, render_template, jsonify # type: ignore
import google.generativeai as genai # type: ignore
import os
from model_setting import *
import vertexai # type: ignore
from vertexai.preview.vision_models import ImageGenerationModel # type: ignore

app = Flask(__name__)

# API Key for genai
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

PROJECT_ID = "geminidiary"  # @param {type:"string"}
LOCATION = "us-central1" # @param {type:"string"}
vertexai.init(project=PROJECT_ID, location=LOCATION)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    # 從前端取得文字和圖片
    contents = request.form['text']
    images = request.files.getlist('images')  # 假設前端傳送多張圖片

    # Step 1: 使用 text 模型生成中文 dump-prompt 和建議
    model = genai.GenerativeModel(model_name="gemini-1.5-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)
    chat = model.start_chat(history=[])

    text_prompts = ''.join([f"""## 日期：{content.date}\n
                            ### 事件：{content.event_summary}\n
                            ### 心得：{content.text}\n""" for content in contents])
    image_prompts = [genai.upload_file(path=image.path, display_name=image.name)
                for image in images]

    prompt_parts = [
        system_message,
        text_prompts,
        *image_prompts,
    ]
    response = model.generate_content(prompt_parts)
    photo_dump = response.text.split("##")[1]
    summarize = response.text.split("##")[2]

    # Step 2: 提取生成的中文總結和 dump-prompt
    photo_dump = response.text.split("##")[1]
    summarize = response.text.split("##")[2]

    # Step 3: 將中文 dump-prompt 翻譯成英文（假設使用翻譯模型）
    translate_model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                              generation_config=generation_config,
                              safety_settings=safety_settings)
    translation_response = translate_model.generate_content([translate_system_message, photo_dump])
    dump_prompt = translation_response.text

    # Step 4: 使用 image 模型生成圖片
    imagen_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
    
    # 生成圖片
    dump_response = imagen_model.generate_images(
      prompt= + dump_prompt,
      aspect_ratio="16:9",
      person_generation="dont_allow"
    )
    
    # Step 5: 將圖片和總結返回前端
    dump_image = dump_response.images[0]
    dump_image.save("dump_image.png")

    # 將總結和圖片一起返回給前端
    return jsonify({'summary': summarize, 'image_url': 'dump_image.png'})

if __name__ == '__main__':
    app.run(debug=True)
