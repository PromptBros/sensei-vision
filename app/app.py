from flask import (
    Flask,
    render_template,
    request,
    Response,
    stream_with_context,
    jsonify,
)
from openai import OpenAI

import os

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

import base64

app = Flask(__name__)

# Initial chat history - Please adjust system prompt for necessary context
chat_history = [
    {
        "role": "system",
        "content": "These are frames from a video that I want to upload. Generate a compelling description that I can upload along with the video.",
    },
]


def encode_image(image_file):

    return base64.b64encode(image_file.read()).decode("utf-8")


@app.route("/", methods=["GET"])
def index():

    return render_template("index.html", chat_history=chat_history)


@app.route("/chat", methods=["POST"])
def chat():

    data = request.json

    message_text = data.get("message", "")

    images = data.get("images", [])  # Expect base64 encoded images

    # Prepare the message content

    content = []

    # Add text if present

    if message_text:

        content.append({"type": "text", "text": message_text})

    # Add images if present
    for image in images:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image}"},
            }
        )

    # Add to chat history
    chat_history.append({"role": "user", "content": content})

    return jsonify(success=True)


@app.route("/stream", methods=["GET"])
def stream():

    def generate():

        assistant_response_content = ""

        with client.chat.completions.create(
            model="gpt-4o",  # Make sure to use the vision model
            messages=chat_history,
            stream=True,
            max_tokens=4096,  # Adjust as needed
        ) as stream:

            for chunk in stream:

                if chunk.choices[0].delta and chunk.choices[0].delta.content:

                    assistant_response_content += chunk.choices[0].delta.content

                    yield f"data: {chunk.choices[0].delta.content}\n\n"

                if chunk.choices[0].finish_reason == "stop":

                    break

        chat_history.append(
            {"role": "assistant", "content": assistant_response_content}
        )

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/reset", methods=["POST"])
def reset_chat():

    global chat_history

    chat_history = [
        {
            "role": "system",
            "content": "These are frames from a video that I want to upload. Generate a compelling description that I can upload along with the video.",
        }
    ]

    return jsonify(success=True)
