import cv2
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import time
from threading import Thread
# Import necessary libraries
from flask import Flask, render_template, Response
# Initialize the Flask app
app = Flask(__name__, template_folder='template')
time.sleep(10)
app.static_folder = 'static'
KNOWN_DISTANCE = 72.4  # centimeter
# width of face in the real world or Object Plane
KNOWN_WIDTH = 13.8  # centimeter
# Colors
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
fonts = cv2.FONT_HERSHEY_COMPLEX
# cap = cv2.VideoCapture(0)

# face detector object
face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def focal_length(measured_distance, real_width, width_in_rf_image):
    """
    This Function Calculate the Focal Length(distance between lens to CMOS sensor), it is simple constant we can find by using
    MEASURED_DISTACE, REAL_WIDTH(Actual width of object) and WIDTH_OF_OBJECT_IN_IMAGE
    :param1 Measure_Distance(int): It is distance measured from object to the Camera while Capturing Reference image

    :param2 Real_Width(int): It is Actual width of object, in real world (like My face width is = 14.3 centimeters)
    :param3 Width_In_Image(int): It is object width in the frame /image in our case in the reference image(found by Face detector)
    :retrun focal_length(Float):"""
    focal_length_value = (width_in_rf_image * measured_distance) / real_width
    return focal_length_value

# distance estimation function


def distance_finder(focal_length, real_face_width, face_width_in_frame):
    """
    This Function simply Estimates the distance between object and camera using arguments(focal_length, Actual_object_width, Object_width_in_the_image)
    :param1 focal_length(float): return by the focal_length_Finder function

    :param2 Real_Width(int): It is Actual width of object, in real world (like My face width is = 5.7 Inches)
    :param3 object_Width_Frame(int): width of object in the image(frame in our case, using Video feed)
    :return Distance(float) : distance Estimated
    """
    distance = (real_face_width * focal_length) / face_width_in_frame
    return distance


def face_data(image):
    """
    This function Detect the face
    :param Takes image as argument.
    :returns face_width in the pixels
    """

    face_width = 0
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray_image, 1.3, 5)
    for (x, y, h, w) in faces:
        cv2.rectangle(image, (x, y), (x + w, y + h), GREEN, 1)
        face_width = w

    return face_width


def SendMail(ImgFileName="intruder.png"):
    with open(ImgFileName, 'rb') as f:
        img_data = f.read()

    msg = MIMEMultipart()
    msg['Subject'] = 'Intruder in premisis'
    msg['From'] = 'harsh.ku.spam@gmail.com'
    msg['To'] = 'harsh.ku.work@gmail.com'

    text = MIMEText("Please check the premiss \n for your saefty")
    msg.attach(text)
    image = MIMEImage(img_data, name=os.path.basename(ImgFileName))
    msg.attach(image)

    s = smtplib.SMTP("smtp.gmail.com", 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login("harsh.ku.spam@gmail.com", "password")
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    s.quit()


# reading reference image from directory
ref_image = cv2.imread("/home/harsh/Documents/harsh.png")
# cv2.imshow("ref_image", ref_image)
ref_image_face_width = face_data(ref_image)
focal_length_found = focal_length(
    KNOWN_DISTANCE, KNOWN_WIDTH, ref_image_face_width)
print(focal_length_found)
# cv2.imshow("ref_image", ref_image)

cap = cv2.VideoCapture(0)


def inspection():
    print("inspection")
    while True:
        success, frame = cap.read()  # read the camera frame
        if not success:
            break
        else:
            face_width_in_frame = face_data(frame)
#     finding the distance by calling function Distance
            Distance = 157
            if face_width_in_frame != 0:
                Distance = distance_finder(
                    focal_length_found, KNOWN_WIDTH, face_width_in_frame)
        # Drwaing Text on the screen
                cv2.putText(
                    frame, f"Distance = {round(Distance,2)} CM", (50,
                                                                  50), fonts, 1, (GREEN), 2
                )
            if Distance < 150:
                cv2.imwrite("intruder.png", frame)
                SendMail()
                print("Sending Email")
                time.sleep(3*60)


def gen_frames():
    while True:
        success, frame = cap.read()  # read the camera frame
        if not success:
            break
        else:
            face_width_in_frame = face_data(frame)
#     finding the distance by calling function Distance
            Distance = 157
            if face_width_in_frame != 0:
                Distance = distance_finder(
                    focal_length_found, KNOWN_WIDTH, face_width_in_frame)
        # Drwaing Text on the screen
                cv2.putText(
                    frame, f"Distance = {round(Distance,2)} CM", (50,
                                                                  50), fonts, 1, (GREEN), 2
                )
            if Distance < 150:
                cv2.imwrite("intruder.png", frame)
#                 SendMail()
#                 print("Sending Email")
#                 time.sleep(3*60)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


def FlaskThread():
    app.run(debug=True, use_reloader=False)
# def twinFunction(cap):
#     t1 = Thread(target=inspection(cap))
#     t2 = Thread(target=gen_frames(cap))
#     t1.setDaemon(True)
#     t1.start()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():

    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def video_inspect():
    print("inspection")
    inspection()


@app.route("/forward")
def move_forward():
    # Moving forward code
    forward_message = "Moving Forward..."
    return render_template('index.html', forward_message=forward_message)


if __name__ == "__main__":
    # Thread(app.run(debug=True))
    t1 = Thread(target=FlaskThread)
    t2 = Thread(target=inspection)
    # t1.setDaemon(True)
    # t2.setDaemon(True)
    t2.start()
    t1.start()
