import mss
import cv2
import base64
import requests

def take_screenshot():
    with mss.mss() as s:
        monitor = s.monitors[1]
        screenshot = s.grab(monitor)
        img = cv2.cvtColor(cv2.imdecode(np.frombuffer(screenshot.rgb, np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        return img


def screenshot_to_base64(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')


def analyze_screen(query):
    image = take_screenshot()
    encoded_image = screenshot_to_base64(image)
    response = requests.post('https://your-groq-api-endpoint', json={'image': encoded_image, 'query': query})
    return response.json()