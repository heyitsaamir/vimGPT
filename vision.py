import base64
import json
import os
from io import BytesIO

import openai
from dotenv import load_dotenv
from PIL import Image
from typing import Union

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
IMG_RES = 1080


# Function to encode the image
def encode_and_resize(image):
    W, H = image.size
    image = image.resize((IMG_RES, int(IMG_RES * H / W)))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded_image


def get_actions(screenshot, objective, completion_condition = Union[str, None]):
    # raise NotImplementedError("This function is not implemented yet.")
    encoded_screenshot = encode_and_resize(screenshot)
    # if completion condition is not none, then use it other wise use When the page seems satisfactory,
    completion_condition_str = f"When the completion condition ({completion_condition}) seems to be satisfiedm" if completion_condition else "When the page seems satisfactory, "
    response = openai.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"You need to choose which action to take to help a user do this task: {objective}. Your options are navigate, type, click, and done. Navigate should take you to the specified URL. Type and click take strings where if you want to click on an object, return the string with the yellow character sequence you want to click on, and to type just a string with the message you want to type. For clicks, only respond with the 1-2 letter sequence in the yellow box. If there are multiple valid options choose the one you think a user would select. For typing, return a click to click on the box along with a type with the message to write. {completion_condition_str} return done as a key with no value. You must respond in JSON only with no other fluff or bad things will happen. The JSON keys must ONLY be one of navigate, type, or click. Do not return the JSON inside a code block.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_screenshot}",
                        },
                    },
                ],
            }
        ],
        max_tokens=100,
    )

    try:
        json_response = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        print("Error: Invalid JSON response" + json.dumps(response.choices))
        cleaned_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant to fix an invalid JSON response. You need to fix the invalid JSON response to be valid JSON. You must respond in JSON only with no other fluff or bad things will happen. Do not return the JSON inside a code block.",
                },
                {"role": "user", "content": f"The invalid JSON response is: {response.choices[0].message.content}"},
            ],
        )
        try:
            cleaned_json_response = json.loads(cleaned_response.choices[0].message.content)
        except json.JSONDecodeError:
            print("Error: Invalid JSON response" + json.dumps(cleaned_response.choices))
            return {}
        return cleaned_json_response

    return json_response


if __name__ == "__main__":
    image = Image.open("image.png")
    actions = get_actions(image, "upvote the pinterest post")
