import cv2
import numpy as np

PHOTO_SPECS = {
    "1inch": {"width": 295, "height": 413, "label": "1寸 (25×35mm)"},
    "s1inch": {"width": 260, "height": 378, "label": "小1寸 (22×32mm)"},
    "2inch": {"width": 413, "height": 579, "label": "2寸 (35×49mm)"},
    "s2inch": {"width": 413, "height": 531, "label": "小2寸 (35×45mm)"},
    "big1inch": {"width": 390, "height": 567, "label": "大一寸 (33×48mm)"},
}

LAYOUT_PRESETS = {
    "1inch": {"cols": 4, "rows": 2},
    "s1inch": {"cols": 4, "rows": 2},
    "2inch": {"cols": 2, "rows": 2},
    "s2inch": {"cols": 2, "rows": 2},
    "big1inch": {"cols": 3, "rows": 2},
}

PAPER_6INCH_W = 1800
PAPER_6INCH_H = 1200
PAPER_PADDING = 10
PHOTO_SPACING = 10


class PhotoCropper:

    @staticmethod
    def crop_and_resize(
        image_data: bytes,
        x: float, y: float, w: float, h: float,
        target_w: int, target_h: int
    ) -> bytes:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        height, width = img.shape[:2]

        px = max(0, int(x * width))
        py = max(0, int(y * height))
        pw = min(width - px, int(w * width))
        ph = min(height - py, int(h * height))

        if pw < 10 or ph < 10:
            _, buf = cv2.imencode(".png", img)
            return buf.tobytes()

        cropped = img[py:py+ph, px:px+pw]
        resized = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

        _, buf = cv2.imencode(".png", resized)
        return buf.tobytes()

    @staticmethod
    def generate_layout(
        image_data: bytes,
        spec: str
    ) -> bytes:
        if spec not in PHOTO_SPECS or spec not in LAYOUT_PRESETS:
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            _, buf = cv2.imencode(".png", img)
            return buf.tobytes()

        spec_data = PHOTO_SPECS[spec]
        layout = LAYOUT_PRESETS[spec]
        pw, ph = spec_data["width"], spec_data["height"]
        cols, rows = layout["cols"], layout["rows"]

        nparr = np.frombuffer(image_data, np.uint8)
        photo = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        photo = cv2.resize(photo, (pw, ph), interpolation=cv2.INTER_LANCZOS4)

        canvas = np.ones((PAPER_6INCH_H, PAPER_6INCH_W, 3), dtype=np.uint8) * 255

        for row in range(rows):
            for col in range(cols):
                ox = PAPER_PADDING + col * (pw + PHOTO_SPACING)
                oy = PAPER_PADDING + row * (ph + PHOTO_SPACING)
                if ox + pw <= PAPER_6INCH_W and oy + ph <= PAPER_6INCH_H:
                    canvas[oy:oy+ph, ox:ox+pw] = photo

        _, buf = cv2.imencode(".png", canvas)
        return buf.tobytes()