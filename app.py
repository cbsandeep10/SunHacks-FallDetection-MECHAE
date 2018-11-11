import os
from flask import Flask, render_template, Response
from camera import VideoCamera

app = Flask(__name__)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/sandeepbalaji/imagerec-f4937063c0eb.json"
camera = VideoCamera()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/renders')
def renders():
    return render_template('carousel.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
