import flask 
from flask import request
import os
from .bot import Bot, QuoteBot, ImageProcessingBot
import boto3
from flask import jsonify

app = flask.Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
BOT_APP_URL = os.environ['BOT_APP_URL']


@app.route('/', methods=['GET'])
def index():
    return 'Ok'


@app.route(f'/{TELEGRAM_BOT_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    bot.handle_message(req['message'])
    return 'Ok'


@app.route("/predictions/<prediction_id>", methods=["POST"])
def get_prediction(prediction_id):
    data = request.get_json()
    chat_id = data.get("chat_id")
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    prediction_table = dynamodb.Table('HaithamPredictionSessions')
    detection_table = dynamodb.Table('HaithamDetectionSessions')
    print (f"Returning chatID : {chat_id}")
    try:
        prediction = prediction_table.get_item(Key={'uid': prediction_id}).get('Item')
        if not prediction:
            return jsonify({"error" : "Prediction not found"}), 404
                
    # Get detection objects
        query_response = detection_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('prediction_uid').eq(prediction_id)
        )
        detection_objects = query_response.get('Items', [])

        data ={
            "uid": prediction_id,
            "original_image": prediction.get("original_image"),
            "predicted_image": prediction.get("predicted_image"),
            "detection_objects": [
                {
                    "label": obj["label"],
                    "score": float(obj["score"]),
                    "box": obj["box"]
                } for obj in detection_objects
            ]
        }
    except Exception as e:
        return jsonify({"error": f"SDynamoDB error: {str(e)}"}), 500
        
    if prediction_id:
        if data:
            data = data.json()
            detection_objects = data.get("detection_objects", [])
            labels = [obj["label"] for obj in detection_objects]
            detection_msg = f"Detected objects:\n" + "\n".join(labels) if labels else "No objects detected."
            bot.send_text(chat_id, detection_msg)
            return jsonify({"status": "ok"})
        else:
            bot.send_text(chat_id, f"YOLO server error: {request.status_code}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500









if __name__ == "__main__":
    bot = ImageProcessingBot(TELEGRAM_BOT_TOKEN, BOT_APP_URL)

    app.run(host='0.0.0.0', port=8443)
