import barcode
import qrcode
from barcode.writer import ImageWriter
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.encoding import smart_str
from time import sleep

from .models import *
from django.core.mail import EmailMessage
from django.views.decorators import gzip
from django.http import StreamingHttpResponse
import cv2
import threading
import os

var1 = 0

# Create your views here.
def generate(request):
    context = {
        'barcode_types': ['qrcode'] + [b for b in barcode.PROVIDED_BARCODES if str(b).startswith('code')] 
    }

    if request.method == 'POST':
        
        var1 = 1

        b_type = request.POST['typeOfBarcode']
        b_data = request.POST['barcodeData']
        n_data = request.POST['Name']

        def generate_file(barcode_file):
            # output = HttpResponse(content_type="image/jpeg")
            output = HttpResponse(content_type="application/force-download")
            barcode_file.save(output, "JPEG")
            output['Content-Disposition'] = 'attachment; filename=%s' % smart_str('barcode.jpg')
            output['X-Sendfile'] = smart_str(f'{b_data}.jpg')
            return output

        if b_type == 'qrcode':
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=1,
            )
            qr.add_data(b_data)
            qr.make(fit=True)
            qr_file = qr.make_image(fill_color="black", back_color="white") # render qr image
            return generate_file(qr_file) # generate the file

        else:        
            bar = barcode.get_barcode(name=b_type, code=b_data, writer=ImageWriter())
            barcode_file = bar.render() # creates a PIL class image object
            return generate_file(barcode_file) # generate the file
            
    else:
        return render(request, 'generate_barcodes/generate.html', context=context)
    
#===================================================================

@gzip.gzip_page
def Home(request):
    try:
        cam = VideoCamera()
        return StreamingHttpResponse(gen(cam), content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        pass
    return render(request, 'generate_barcode/generate.html')

#to capture video class
class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(int(os.environ.get('CAMERA')))
        (self.grabbed, self.frame) = self.video.read()
        threading.Thread(target=self.update, args=()).start()
        
    def __del__(self):
        self.video.release()

    def get_frame(self):
        image = self.frame
        _, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
    
    def picture(self, data):
            frame = self.video.read()
            cv2.imwrite(f'C:\\Users\\eduar\\Desktop\\Programação\\Django-OpenCV-Barcodes-main\\images\\{data}.png', frame)

    def update(self):
        while True:
            (self.grabbed, self.frame) = self.video.read()

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

