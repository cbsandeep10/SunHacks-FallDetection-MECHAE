import cv2
import threading
import json
from time import time
from google.cloud import storage
from datetime import datetime
from twilio.rest import Client
from google.cloud import automl_v1beta1 as automl

bucket_name = 'fall-bucket'
project_id = 'imagerec-222202'
compute_region = 'us-central1'
model_id = 'ICN6080161874241715877'
score_threshold = '0.5'
automl_client = automl.AutoMlClient()

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.get_bucket(bucket_name)
        self.time = time()
        self.stand = 0
        self.fall = 0
        self.done = True

    def __del__(self):
        self.video.release()

    def predictClass(self, jpeg):
        # Get the full path of the model.
        model_full_id = automl_client.model_path(
            project_id, compute_region, model_id
        )
        # Create client for prediction service.
        prediction_client = automl.PredictionServiceClient()
        payload = {"image": {"image_bytes": jpeg}}

        params = {}
        if score_threshold:
            params = {"score_threshold": score_threshold}
        response = prediction_client.predict(model_full_id, payload, params)
        res = {}
        for result in response.payload:
            res[result.display_name] = result.classification.score
            if result.display_name == "fall":
                self.fall += 1
            elif result.display_name == "stand":
                self.stand += 1

        # Uploading to storage
        name = str(datetime.now()).replace(" ","") + '.jpg'
        blob = self.bucket.blob(name)
        blob.upload_from_string(jpeg)
        blob = self.bucket.blob(name.replace(".jpg", ".json"))
        blob.upload_from_string(json.dumps(res))
        if self.stand < 4 and self.stand > 0:
            self.get_images(name, "static/images/stand-0"+str(self.stand)+".jpg")
            print(name, res)
        elif self.fall < 4 and self.fall > 0:
            self.get_images(name, "static/images/fall-0"+str(self.fall)+".jpg")
            print(name, res)
        if self.fall > 4 and self.done:
            self.done = False
            account_sid = 'ACb7fcbdfdd696b6395691d777af1539b2'
            auth_token = 'eb69fd893fb3d3f664692efcc16cbaa9'
            client = Client(account_sid, auth_token)
            message = client.messages \
                           .create(
                                body="Take care of your dear ones!!",
                                from_='+14092456334',
                                to='+14805775641'
                            )
            print(message.sid)

    def get_images(self, name, type):
        blob = self.bucket.blob(name)
        blob.download_to_filename(type)

    def get_frame(self):
        success, image = self.video.read()
        ret, jpeg = cv2.imencode('.jpg', image)
        if time() > self.time + 1:
            t = threading.Thread(target=self.predictClass, args=(jpeg.tobytes(),))
            t.start()
            self.time = time()
        return jpeg.tobytes()
