import cv2
import numpy as np


class WatermarkProcessor:

    @staticmethod
    def remove_watermark_auto(
        image_data: bytes,
        watermark_region: dict | None = None
    ) -> bytes:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        mask = WatermarkProcessor._build_precise_text_mask(img, watermark_region)

        if np.sum(mask) < 100:
            result = img
        else:
            result = WatermarkProcessor._inpaint_precise(img, mask)

        _, buffer = cv2.imencode(".png", result)
        return buffer.tobytes()

    @staticmethod
    def _build_precise_text_mask(img: np.ndarray, watermark_region: dict | None) -> np.ndarray:
        height, width = img.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)

        if watermark_region and watermark_region.get("w", 0) > 0:
            x = max(0, int(watermark_region["x"] * width))
            y = max(0, int(watermark_region["y"] * height))
            w = min(width - x, int(watermark_region["w"] * width))
            h = min(height - y, int(watermark_region["h"] * height))
            roi = img[y:y+h, x:x+w]
            roi_mask = WatermarkProcessor._extract_text_pixels(roi)
            mask[y:y+h, x:x+w] = roi_mask
        else:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            bottom = gray[int(height * 0.88):, :]
            bottom_color = img[int(height * 0.88):, :]
            y_start = int(height * 0.88)
            bottom_mask = WatermarkProcessor._extract_text_pixels(bottom_color, bottom)
            mask[y_start:, :] = bottom_mask

        return mask

    @staticmethod
    def _extract_text_pixels(roi: np.ndarray, roi_gray: np.ndarray | None = None) -> np.ndarray:
        if roi_gray is None:
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        h, w = roi_gray.shape[:2]
        if h < 20 or w < 20:
            return np.zeros((h, w), dtype=np.uint8)

        edges_low = cv2.Canny(roi_gray, 50, 150)

        adaptive = cv2.adaptiveThreshold(
            roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 21, 12
        )

        _, otsu = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        binary = cv2.bitwise_or(adaptive, otsu)

        edge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        edges_dilated = cv2.dilate(edges_low, edge_kernel, iterations=1)

        combined = cv2.bitwise_and(binary, edges_dilated)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(combined, connectivity=8)
        min_area = 30
        filtered = np.zeros_like(combined)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= min_area:
                filtered[labels == i] = 255
        combined = filtered

        text_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (6, 2))
        combined = cv2.dilate(combined, text_kernel, iterations=1)
        combined = cv2.erode(combined, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 2)), iterations=1)

        combined = cv2.dilate(combined, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2)), iterations=1)

        bright_mask = (roi_gray > 180).astype(np.uint8) * 255
        dark_non_edge = cv2.bitwise_and(binary, cv2.bitwise_not(edges_dilated))
        combined = cv2.bitwise_or(combined, cv2.bitwise_and(dark_non_edge, bright_mask))

        combined = cv2.dilate(combined, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), iterations=1)

        return combined

    @staticmethod
    def _inpaint_precise(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
        return WatermarkProcessor._inpaint_cv2(img, mask)

    @staticmethod
    def _inpaint_cv2(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        mask_rows = np.any(mask > 0, axis=1)
        if not np.any(mask_rows):
            return img.copy()
        first_row = int(np.argmax(mask_rows))
        last_row = h - int(np.argmax(mask_rows[::-1]))

        pad_top = 5
        pad_bottom = 5
        roi_top = max(0, first_row - pad_top)
        roi_bottom = min(h, last_row + pad_bottom)

        roi = img[roi_top:roi_bottom, :]
        roi_mask = mask[roi_top:roi_bottom, :]

        roi_result = cv2.inpaint(roi, roi_mask, 3, cv2.INPAINT_TELEA)
        roi_mask2 = cv2.dilate(roi_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)), iterations=1)
        roi_result = cv2.inpaint(roi_result, roi_mask2, 5, cv2.INPAINT_NS)

        result = img.copy()
        result[roi_top:roi_bottom, :] = roi_result
        return result

    @staticmethod
    def _detect_text_regions(img: np.ndarray):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape[:2]
        bottom_strip = gray[int(height * 0.88):, :]

        _, binary = cv2.threshold(bottom_strip, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (8, 2))
        dilated = cv2.dilate(binary, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        text_contours = [c for c in contours if cv2.contourArea(c) > 50][:8]

        if not text_contours:
            return None

        all_boxes = [cv2.boundingRect(c) for c in text_contours]
        min_x = min(b[0] for b in all_boxes)
        min_y = min(b[1] for b in all_boxes)
        max_x = max(b[0] + b[2] for b in all_boxes)
        max_y = max(b[1] + b[3] for b in all_boxes)

        total_y = int(height * 0.88)
        x1 = max(0, min_x - 2)
        y1 = max(0, total_y + min_y - 2)
        x2 = min(width, max_x + 2)
        y2 = min(height, total_y + max_y + 2)

        return (x1, y1, x2 - x1, y2 - y1)

    @staticmethod
    def remove_watermark_manual(
        image_data: bytes,
        brush_regions: list[dict]
    ) -> bytes:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        height, width = img.shape[:2]

        mask = np.zeros((height, width), dtype=np.uint8)
        for region in brush_regions:
            x = max(0, int(region.get("x", 0) * width))
            y = max(0, int(region.get("y", 0) * height))
            w = min(width - x, int(region.get("w", 0.05) * width))
            h = min(height - y, int(region.get("h", 0.05) * height))
            mask[y:y+h, x:x+w] = 255

        result = WatermarkProcessor._inpaint_precise(img, mask)
        _, buffer = cv2.imencode(".png", result)
        return buffer.tobytes()

    @staticmethod
    def remove_watermark_manual_with_mask(
        image_data: bytes,
        mask_img: np.ndarray | None
    ) -> bytes:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if mask_img is None or np.sum(mask_img) < 100:
            _, buffer = cv2.imencode(".png", img)
            return buffer.tobytes()

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_img = cv2.dilate(mask_img, kernel, iterations=1)

        result = WatermarkProcessor._inpaint_cv2(img, mask_img)
        _, buffer = cv2.imencode(".png", result)
        return buffer.tobytes()

    @staticmethod
    def detect_watermark_region(image_data: bytes) -> dict:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        height, width = img.shape[:2]

        result = WatermarkProcessor._detect_text_regions(img)

        if result:
            x1, y1, w, h = result
            return {
                "detected": True,
                "region": {
                    "x": x1 / width,
                    "y": y1 / height,
                    "w": w / width,
                    "h": h / height
                },
                "confidence": 0.85
            }

        return {"detected": False, "region": None, "confidence": 0.0}


watermark_processor = WatermarkProcessor()