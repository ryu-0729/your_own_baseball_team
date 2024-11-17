import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import openai
import json
import uuid
import base64

# ボットトークンを渡してアプリを初期化します
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

openai.api_key = os.environ.get("OPEN_AI_API_KEY")


@app.event("app_mention")
def handle_mention(event, say):
    user = event["user"]
    text = event.get("text", "")
    bot_user_id = app.client.auth_test()["user_id"]

    text = text.replace(f"<@{bot_user_id}>", "").strip()
    print(f"{text=}")

    say(f"こんにちは、<@{user}> さん！\n入力されたテキスト: {text}")

    nlb_member_lineup_list = generate_nlb_member_lineup(text)
    image_path = generate_nlb_member_lineup_image('\n'.join(nlb_member_lineup_list))
    # TODO: image_pathのimageをslackに投稿
    nlb_member_lineup_text = ""
    for member in nlb_member_lineup_list:
        nlb_member_lineup_text += f"{member}\n"

    say(nlb_member_lineup_text)


def generate_nlb_member_lineup(input_prompt):
    response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
        "role": "system",
        "content": [
            {
            "type": "text",
            "text": "あなたは日本プロ野球の選手で打順をつくる人です。\nテーマに沿ってjson形式でプロ野球の打順を作成してください。\nただし、必ず9人で打順を組んでください\n---\n[\n\"1番（ポジション）：球団：選手名\",\n\"2番（ポジション）：球団：選手名\",\n\"3番（ポジション）：球団：選手名\",\n\"4番（ポジション）：球団：選手名\",\n\"5番（ポジション）：球団：選手名\",\n\"6番（ポジション）：球団：選手名\",\n\"7番（ポジション）：球団：選手名\",\n\"8番（ポジション）：球団：選手名\",\n\"9番（ポジション）：球団：選手名\"\n]"
            }
        ]
        },
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": input_prompt
            }
        ]
        }
    ],
    temperature=1,
    max_tokens=1013,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    tools=[
        {
        "type": "function",
        "function": {
            "name": "create_lineup",
            "description": "Generate a baseball lineup for Japanese professional baseball with 9 players.",
            "parameters": {
            "type": "object",
            "required": [
                "lineup"
            ],
            "properties": {
                "lineup": {
                "type": "array",
                "description": "Array representing the batting order and positions of players",
                "items": {
                    "type": "string",
                    "description": "String format of batting position and player name, e.g., '1番（ポジション）：球団：選手名'"
                }
                }
            },
            },
        }
        }
    ],
    response_format={
        "type": "json_object"
    }
    )

    json_data = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
    return json_data['lineup']

def generate_nlb_member_lineup_image(lineup_list):
    image_path = f"./lineup_image/{uuid.uuid4()}.png"
    response = openai.images.generate(
        model="dall-e-3",
        prompt=lineup_list + "リストの特徴を活かしたポスターの画像生成お願いします。",
        n=1,  # 生成数
        size="1024x1024",
        response_format="b64_json",
        quality="hd",
        style="vivid"
        )
    for chunk in enumerate(response.data):
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(chunk.b64_json))
    return image_path


if __name__ == "__main__":
    # アプリを起動して、ソケットモードで Slack に接続します
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
