import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
from .img_proc import Img
import requests
import boto3
from pydantic import BaseModel
import json
from botocore.exceptions import ClientError
import flask
from flask import request
from flask import Flask , jsonify

app = Flask(__name__)
@app.route("/predictions/<prediction_id>", methods=["POST"])
def get_prediction(self,prediction_id):
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
        request = detection_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('prediction_uid').eq(prediction_id)
        )
        detection_objects = request.get('Items', [])

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
            self.send_text(chat_id, detection_msg)
            return jsonify({"status": "ok"})
        else:
            self.send_text(chat_id, f"YOLO server error: {request.status_code}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500












class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)
        self.s3_bucket_name = 'haitham-polybot-dev'
        self.s3_client = boto3.client('s3')
        self.yolo_url = os.environ['YOLO_SERVER_URL']
        

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/',timeout=60,certificate=open("/app/polybotdev.crt", 'rb'))

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path
    def upload_to_s3(self, local_file_path, s3_key):
        self.s3_client.upload_file(local_file_path, self.s3_bucket_name, s3_key)

    app = Flask(__name__)
    @app.route("/predictions/<prediction_id>", methods=["POST"])
    def get_prediction(self,prediction_id):
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
            request = detection_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('prediction_uid').eq(prediction_id)
            )
            detection_objects = request.get('Items', [])

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
                self.send_text(chat_id, detection_msg)
                return jsonify({"status": "ok"})
            else:
                self.send_text(chat_id, f"YOLO server error: {request.status_code}")
                return jsonify({"error": f"Server error: {str(e)}"}), 500
                



    class ImageNameRequest(BaseModel):
        image_name: str
    

    def notify_yolo_service(self, image_name,chat_id):
        payload = self.ImageNameRequest(image_name=image_name).dict()
        payload["chat_id"] = chat_id
        sqs = boto3.client('sqs', region_name='us-east-1')
        QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/228281126655/haitham-polybot-chat-messages'
        try:
            sqs_response = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(payload))
            print(f"Message sent successfully. MessageId: {sqs_response['MessageId']}")
            return {
                "status": "success",
                "sqs_message_id": sqs_response['MessageId'],
                }
        except ClientError as e:
                print(f"Error sending message: {e}")
                return {"error": "Failed to send message to SQS", "details": str(e)}
        except requests.RequestException as e:
            print(f"Error notifying YOLO service: {e}")
            return {"error": "Failed to notify YOLO service", "details": str(e)}
        # send to the client - "Opps, something went wrong. Please try again later."

    

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])



class ImageProcessingBot(Bot):
    def handle_message(self, msg):
        try:
            chat_id = msg['chat']['id']
            print("Message received")

            # media_groups to handle Concat
            if not hasattr(self, 'media_groups'):
                self.media_groups = {}

            if 'photo' in msg:
                caption = msg.get('caption', '').strip()
                media_group_id = msg.get('media_group_id')

                # Handle media group for 'Concat'
                if media_group_id:
                    if media_group_id not in self.media_groups:
                        self.media_groups[media_group_id] = []

                    self.media_groups[media_group_id].append(msg)

                    if len(self.media_groups[media_group_id]) < 2:
                        print("Waiting for more photos in media group...")
                        return  # wait for second photo

                    # Got both images
                    msgs = self.media_groups.pop(media_group_id)
                    caption = msgs[0].get('caption', '').strip()

                    if caption != 'Concat':
                        self.send_text(chat_id, "Expected caption: 'Concat'")
                        return

                    img1 = Img(self.download_user_photo(msgs[0]))
                    img2 = Img(self.download_user_photo(msgs[1]))
                    img1.concat(img2)
                    processed_path = img1.save_img()
                    self.send_photo(chat_id, processed_path)
                    return

                # Single-photo logic
                photo_path = self.download_user_photo(msg)
                img = Img(photo_path)



                if caption == 'Detect':
                    s3_key = photo_path
                    self.upload_to_s3(photo_path, s3_key)
                    notify_result = self.notify_yolo_service(s3_key,chat_id)
                    if notify_result["status"] == "success":
                        return
                elif caption == 'Blur':
                    img.blur()
                elif caption == 'Contour':
                    img.contour()
                elif caption == 'Rotate':
                    img.rotate()
                elif caption == 'Segment':
                    img.segment()
                elif caption == 'Salt and pepper':
                    img.salt_n_pepper()
                else:
                    self.send_text(chat_id, "Unknown or missing caption.")
                    processed_path = img.save_img()
                    self.send_photo(chat_id, processed_path)
                    
                    return

            elif 'text' in msg:
                super().handle_message(msg)
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            self.send_text(msg['chat']['id'], "Something went wrong.... please try again")    