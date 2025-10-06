import json
from flask import Flask, send_file
from flask_cors import CORS

from PIL import Image
import numpy as np
import potrace

app = Flask(__name__, static_folder='.')
CORS(app)

FRAMES = 200

def png_to_np_array(filename):
    img = Image.open(filename)
    data = np.array(img.getdata()).reshape(img.size[1], img.size[0], 3)
    bindata = np.zeros((img.size[1], img.size[0]), np.uint32)
    for i, row in enumerate(data):
        for j, byte in enumerate(row):
            bindata[img.size[1]-i-1, j] = 1 if sum(byte) < 127*3 else 0
        #     print('###' if bindata[i, j] == 1 else '   ', end='')
        # print()
    return bindata

def png_to_svg(filename):
    data = png_to_np_array(filename)
    bmp = potrace.Bitmap(data)
    path = bmp.trace()
    return path

frame_coords = {}

def process_frame(frame_num):
    if frame_num in frame_coords:
        return frame_coords[frame_num]
    
    latex = []
    path = png_to_svg('frames/frame%d.png' % (frame_num + 1))

    for curve in path.curves:
        segments = curve.segments
        start = curve.start_point
        for segment in segments:
            x0, y0 = start.x, start.y
            if segment.is_corner:
                x1, y1 = segment.c.x, segment.c.y
                x2, y2 = segment.end_point.x, segment.end_point.y
                latex.append('((1-t)%f+t%f,(1-t)%f+t%f)' % (x0, x1, y0, y1))
                latex.append('((1-t)%f+t%f,(1-t)%f+t%f)' % (x1, x2, y1, y2))
            else:
                x1, y1 = segment.c1.x, segment.c1.y
                x2, y2 = segment.c2.x, segment.c2.y
                x3, y3 = segment.end_point.x, segment.end_point.y
                latex.append('((1-t)((1-t)((1-t)%f+t%f)+t((1-t)%f+t%f))+t((1-t)((1-t)%f+t%f)+t((1-t)%f+t%f)),\
                (1-t)((1-t)((1-t)%f+t%f)+t((1-t)%f+t%f))+t((1-t)((1-t)%f+t%f)+t((1-t)%f+t%f)))' % \
                (x0, x1, x1, x2, x1, x2, x2, x3, y0, y1, y1, y2, y1, y2, y2, y3))
            start = segment.end_point

    frame_coords[frame_num] = latex
    return latex

@app.route('/')
def serve_index():
    return send_file('index.html')

@app.route('/api/frames')
def get_frames():
    all_frames = []
    for i in range(FRAMES):
        all_frames.append(process_frame(i))
    return json.dumps(all_frames)

if __name__ == '__main__':
    print("="*60)
    print("Starting Desmos3 Bad Apple Demo Server")
    print("="*60)
    print(f"Server will process {FRAMES} frames on-demand (demo version)")
    print("Full version has 5258 frames but requires faster potrace implementation")
    print("Server starting on http://0.0.0.0:5000")
    print("="*60)
    app.run(host='0.0.0.0', port=5000, debug=False)