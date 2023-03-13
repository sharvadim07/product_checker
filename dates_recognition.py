from typing import Tuple, List, Optional
import logging
import re
# import random
import numpy as np
from tqdm import tqdm
# from PIL import Image
# from io import BytesIO
from skimage import transform
import cv2
import pytesseract
from deskew import determine_skew
from sklearn.feature_extraction.image import extract_patches_2d
from dateutil.parser import parse
from datetime import date
from collections import OrderedDict
from time import time
from os import path

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

DATE_PATTERNS = [
    r'\d{4}[-/.]\d{2}[-/.]\d{2}',  # matches yyyy/mm/dd format
    r'\d{2}[-/.]\d{2}[-/.]\d{4}',  # matches dd/mm/yyyy format
    r'\d{2}[-/.]\d{2}[-/.]\d{2}',  # matches dd/mm/yy format
]
COMPILED_DATE_PATTERNS = [re.compile(patt) for patt in DATE_PATTERNS]
OCR_CONFIG = "--psm 11 --oem 3 -c tessedit_char_whitelist=-./0123456789"

class Setting():
    def __init__(
        self, 
        preblur : bool = False, 
        dilate_iter : int = 0, 
        incr_bright : int = 0,
        blur_level : int = 3, 
        alpha : Optional[float] = None,
        beta : Optional[int] = None,
        angle : int = 0
    ) -> None:
        self._preblur = preblur
        self._dilate_iter = dilate_iter
        self._incr_bright = incr_bright
        self._blur_level = blur_level
        self._thresh = np.zeros(0)
        self._recognized_text = ""
        self._alpha = alpha
        self._beta = beta
        self._angle = angle
    @property
    def thresh(self) -> np.ndarray:
        return self._thresh
    @thresh.setter
    def thresh(
        self,
        img : np.ndarray,
    ) -> None:
        img = img.copy()
        # Rotate
        if self._angle > 0:
            img = (transform.rotate(img, self._angle, mode = "symmetric") * 255).astype(np.uint8)
        # Increasing brightness
        # if self._incr_bright > 0:
        #     img = change_brightness(img, value = self._incr_bright)
        # Brightness and contrast
        cv2.convertScaleAbs(img, img, self._alpha, self._beta)
        # Bluring
        if self._preblur:
            #gray = cv2.GaussianBlur(gray, (11, 11), 0)
            img = cv2.medianBlur(img, self._blur_level)
        self._thresh = img
        # Applying thresholding 
        ret, self._thresh = cv2.threshold(img, 120, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
        # # Padding
        # #self._thresh = cv2.copyMakeBorder(self._thresh, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        if self._dilate_iter > 0:
            # Dilation
            kernel = np.ones((2, 2), 'uint8')
            # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            self._thresh = cv2.dilate(self._thresh, kernel, iterations = self._dilate_iter)
            # Bluring after dilation
            #self._thresh = cv2.GaussianBlur(self._thresh, (9, 9), 0)
            self._thresh = cv2.medianBlur(self._thresh, self._blur_level)
            #self._thresh = cv2.bilateralFilter(self._thresh, 2, 200, 200)
        # # Thresholding after dilation + bluring
        # ret, self._thresh = cv2.threshold(self._thresh, 120, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    @property
    def recognized_text(self) -> str:
        return self._recognized_text
    @recognized_text.setter
    def recognized_text(self, text : str):
        self._recognized_text = text
        self._recognized_text_len = len(re.sub("\n|\s", "", text))
    @property
    def recognized_text_len(self) -> int:
        return self._recognized_text_len
    
# def increase_brightness(img : np.ndarray, value : int = 30) -> np.ndarray:
#     hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
#     h, s, v = cv2.split(hsv)
#     lim = 255 - value
#     v[v > lim] = 255
#     v[v <= lim] += value
#     final_hsv = cv2.merge((h, s, v))
#     img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
#     return img

def bytearray_to_img(downloaded_photo : bytearray) -> np.ndarray:
    return cv2.imdecode(np.frombuffer(downloaded_photo, np.uint8), cv2.IMREAD_COLOR)

def descew_image(img : np.ndarray, data_dir : str) -> Tuple[np.ndarray, Optional[np.float64]]:
    angle = determine_skew(img)
    # Rotation if angle not 0
    if angle:
        img = (transform.rotate(img, angle, mode = "symmetric") * 255).astype(np.uint8)
    # Image.fromarray(img).save(f"{data_dir}/rotated.png")
    return img, angle

def my_ocr(txt_out_filename : str, thresh : np.ndarray) -> str:
    # Apply OCR 
    text = pytesseract.image_to_string(thresh, config=OCR_CONFIG)
    if len(text) > 0:
        # A text file is created and flushed
        with open(txt_out_filename, "a") as out_file:
            # Appending the text into file
            out_file.write(text)
            return text
    else:
        return ''

def check_text(text : str, diff_years : int = 5, min_text_len : int = 6) -> OrderedDict[str, date]:
    res_parsed : OrderedDict[str, date] = OrderedDict()
    if len(text) < min_text_len:
        return res_parsed
    dates_strs : List[str] = []
    for compiled_pattern in COMPILED_DATE_PATTERNS:
        res = compiled_pattern.findall(text)
        if len(res) > 0:
            dates_strs += res
            break
    for date_str in res:
        try:
            parsed_date = parse(date_str, dayfirst = True).date()
            if abs(date.today().year - parsed_date.year) <= diff_years:
                res_parsed[date_str] = parsed_date
                logging.info(parsed_date)
        except ValueError:
            pass
    return res_parsed

def flush_file(txt_out_filename):
    with open(txt_out_filename, "w") as out_file:
        out_file.write('')

def init_settings(shuffling : bool = False, img : np.ndarray = np.ndarray(0)) -> List[Setting]:
    # Initialize settings levels
    settings : List[Setting] = []
    for preblur_level in [False]:
        for brightness_level in [0, -40, 10]:
            for contrast_level in [0.3, 1.5]:
                for dilate_iter_level in [0, 2, 4]:
                    for angle_level in [0, -40, -20, 20, 40]:
                        cur_setting = Setting(preblur = preblur_level, 
                                                dilate_iter = dilate_iter_level, 
                                                alpha = contrast_level,
                                                beta = brightness_level,
                                                angle = angle_level)
                        if img.shape[0] > 0:
                            cur_setting.thresh = img
                        settings.append(cur_setting)
    # if shuffling:
    #     settings = sorted(random.sample(settings, len(settings)), key = lambda v : v._preblur)
        #return random.sample(settings, len(settings))
    return settings

def recognize_full_image(
        settings : List[Setting], 
        recognised_dates : OrderedDict[str, date], 
        data_dir : str,
        max_number_dates : int = 0
    ) -> None:
    recognition_log_file = f"{data_dir}/recognized_log.txt"
    flush_file(recognition_log_file)
    for cur_setting in tqdm(settings):
        # Image.fromarray(cur_setting.thresh).save(f"{data_dir}/full_thresh.png")
        cur_setting.recognized_text = \
            my_ocr(recognition_log_file, cur_setting.thresh)
        if len(cur_setting.recognized_text) > 0:
            recognised_dates.update(check_text(cur_setting.recognized_text))
            if max_number_dates > 0 \
                and len(recognised_dates) >= max_number_dates:
                return
            
def recognize_tiles_image(
        settings : List[Setting],
        recognised_dates : OrderedDict[str, date],
        data_dir : str,
        max_number_dates : int = 0,
        reductions_factors : List[int] = [4],
        settings_num : Optional[int] = None
    ) -> None:
    settings = sorted(
        settings, 
        key = lambda v : v.recognized_text_len, 
        reverse = True
    )
    if settings_num:
        settings = settings[ : settings_num]
    recognition_log_file = f"{data_dir}/recognized_tiles_log.txt"
    flush_file(recognition_log_file)
    for patch_reduction_factor in reductions_factors:
        for cur_setting in tqdm(settings):
            patch_size = sorted(
                            [int(cur_setting.thresh.shape[0]/patch_reduction_factor), 
                                int(cur_setting.thresh.shape[1]/patch_reduction_factor)]
                            )
            for patch in extract_patches_2d(
                    cur_setting.thresh, 
                    patch_size = patch_size, 
                    max_patches = patch_reduction_factor ** 3
                ):
                # Image.fromarray(patch).save(f"{data_dir}/tile_thresh.png")
                text = my_ocr(recognition_log_file, patch)
                if text:
                    recognised_dates.update(check_text(text))
                    if max_number_dates > 0 \
                        and len(recognised_dates) >= max_number_dates:
                        return

def filter_recognised_dates(recognised_dates : OrderedDict[str, date]) -> OrderedDict[str, date]:
    # Do filter dates
    prod_dates, exp_dates = get_possible_prod_exp_dates(recognised_dates)
    if len(prod_dates) > 0 and len(exp_dates) > 0:
        return OrderedDict([prod_dates[-1], exp_dates[0]])
    elif len(prod_dates) >= 2:
        # Exp date before today
        return OrderedDict([prod_dates[-2], prod_dates[-1]])
    elif len(exp_dates) >= 1:
        # Only expiry date has
        return OrderedDict([exp_dates[0]])
    return recognised_dates

def get_possible_prod_exp_dates(recognised_dates : OrderedDict[str, date]) \
    -> Tuple[List[Tuple[str, date]], List[Tuple[str, date]]]:
    dates_before_today : List[Tuple[str, date]] = []
    dates_after_today : List[Tuple[str, date]] = []
    for date_s, date_v in recognised_dates.items():
        if date_v < date.today():
            dates_before_today.append((date_s, date_v))
        else:
            dates_after_today.append((date_s, date_v))
    prod_dates = sorted(dates_before_today, key = lambda v : v[1])
    exp_dates = sorted(dates_after_today, key = lambda v : v[1])
    return prod_dates, exp_dates

def get_prod_exp_dates(recognised_dates : OrderedDict[str, date]) \
    -> Tuple[Optional[Tuple[str, date]], Optional[Tuple[str, date]]]:
    prod_dates, exp_dates = get_possible_prod_exp_dates(recognised_dates)
    # Do filter dates
    if len(prod_dates) > 0 and len(exp_dates) > 0:
        return prod_dates[-1], exp_dates[0]
    elif len(prod_dates) >= 2:
        # Exp date before today
        return prod_dates[-2], prod_dates[-1]
    elif len(prod_dates) >= 1:
        # Only production date has
        return prod_dates[-1], None
    elif len(exp_dates) >= 1:
        # Only expiry date has
        return None, exp_dates[0]
    return None, None

def get_img_from_path(img_path: str) -> Optional[np.ndarray]:
    if not path.exists(img_path):
        return None
    # Read image
    return cv2.imread(img_path)

def img_initial_preparation(img : np.ndarray, data_dir : str):
    # Reduce resolution
    # while min(img.shape) > 800:
    #     img = cv2.pyrDown(img)
    # image to gray
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Rotate
    img, _ = descew_image(img, data_dir)
    return img

def dates_recognition(
        img: np.ndarray, 
        data_dir : str, 
        max_number_dates : int = 2
    ) -> OrderedDict[str, date]:
    recognised_dates = OrderedDict() # type: OrderedDict
    # Image.fromarray(img).save(f"{data_dir}/recieved_image.png")
    # image to gray, resizing, rotation
    img = img_initial_preparation(img, data_dir)
    
    # Init several images views with differecnt settings 
    # Everyone will be used for OCR
    settings = init_settings(shuffling = False, img = img)
    
    # Try to recognize from full image
    recognize_full_image(
        settings = settings, 
        recognised_dates = recognised_dates, 
        data_dir = data_dir,
        max_number_dates = max_number_dates
    )
    logging.info("recognised_dates from full image:")
    logging.info(recognised_dates)

    # Check after full image recognition
    if len(recognised_dates) >= max_number_dates:
        recognised_dates = \
            filter_recognised_dates(recognised_dates = recognised_dates)
        logging.info("filtered recognised_dates:")
        logging.info(recognised_dates)
        return recognised_dates
    elif len(recognised_dates) == 2:
        filtered_recognised_dates = \
            filter_recognised_dates(recognised_dates = recognised_dates)
        if len(filtered_recognised_dates) == 2:
            logging.info("filtered recognised_dates:")
            logging.info(recognised_dates)
            return filtered_recognised_dates

    # Try to recognize from tiles image
    logging.info("will try to recognize from tiles image...")
    recognize_tiles_image(
        settings = settings, 
        recognised_dates = recognised_dates, 
        data_dir = data_dir,
        max_number_dates = max_number_dates,
        settings_num = int(len(settings) / 4)
    )
    logging.info("recognised_dates:")
    logging.info(recognised_dates)
    recognised_dates = \
        filter_recognised_dates(recognised_dates = recognised_dates)
    logging.info("filtered recognised_dates:")
    logging.info(recognised_dates)
    return recognised_dates

def main():
    data_dir = "data/bot_test/"
    img = get_img_from_path(f"{data_dir}/recieved_image.png")
    recognised_dates = dates_recognition(img, data_dir)

if __name__ == "__main__":
    st = time()
    main()
    end = time()
    logging.info("Execution time: {:.6f} seconds".format(end - st))