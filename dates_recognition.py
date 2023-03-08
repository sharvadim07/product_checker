from typing import Tuple, List, Dict, Optional
import re
import random
import numpy as np
from tqdm import tqdm
# from PIL import Imagewhere
from skimage import transform
import cv2
import pytesseract
from deskew import determine_skew
from sklearn.feature_extraction.image import extract_patches_2d
from dateutil.parser import parse
from datetime import date
from datetime import datetime
from collections import OrderedDict
from time import time
from os import path

class Setting():
    def __init__(
        self, 
        preblur : bool = False, 
        dilate_iter : int = 8, 
        incr_bright : int = 0,
        blur_level : int = 5
    ) -> None:
        self._preblur = preblur
        self._dilate_iter = dilate_iter
        self._incr_bright = incr_bright
        self._blur_level = blur_level
        self._thresh = np.ndarray(0)
        self._recognized_text = ""
    @property
    def thresh(self) -> np.ndarray:
        return self._thresh
    @thresh.setter
    def thresh(
        self,
        img : np.ndarray,
    ) -> None:
        img = img.copy()
        # Increasing brightness
        if self._incr_bright > 0:
            img = increase_brightness(img, value = self._incr_bright)
        # image to gray
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if self._preblur:
            # Bluring
            #gray = cv2.GaussianBlur(gray, (11, 11), 0)
            img = cv2.medianBlur(img, self._blur_level)
        # Applying thresholding 
        ret, self._thresh = cv2.threshold(img, 120, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
        # Padding
        #self._thresh = cv2.copyMakeBorder(self._thresh, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        # Dilation
        kernel = np.ones((2, 2), 'uint8')
        # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        self._thresh = cv2.dilate(self._thresh, kernel, iterations = self._dilate_iter)
        # Bluring after dilation
        #self._thresh = cv2.GaussianBlur(self._thresh, (9, 9), 0)
        self._thresh = cv2.medianBlur(self._thresh, self._blur_level)
        #self._thresh = cv2.bilateralFilter(self._thresh, 2, 200, 200)
        # Thresholding after dilation + bluring
        ret, self._thresh = cv2.threshold(self._thresh, 120, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
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
    

def increase_brightness(img : np.ndarray, value : int = 30) -> np.ndarray:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    lim = 255 - value
    v[v > lim] = 255
    v[v <= lim] += value
    final_hsv = cv2.merge((h, s, v))
    img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    return img

def descew_image(img : np.ndarray) -> Tuple[np.ndarray, Optional[np.float64]]:
    angle = determine_skew(img)
    # Descewing
    if angle:
        img = (transform.rotate(img, angle, mode = "symmetric") * 255).astype(np.uint8)
    # Image.fromarray(img).save(f"{data_dir}/rotated.png")
    return img, angle

def my_ocr(txt_out_filename : str, thresh : np.ndarray) -> str:
    # Apply OCR 
    text = pytesseract.image_to_string(
            thresh, 
            config='--psm 11 --oem 3 -c tessedit_char_whitelist=./:0123456789'
            )
    if len(text) > 0:
        # A text file is created and flushed
        with open(txt_out_filename, "a") as out_file:
            # Appending the text into file
            out_file.write(text)
            return text
    else:
        return ''

def check_text(text : str, diff_years : int = 5) -> Dict[str, date]:
    res = re.findall(r"[0-9]{2}\/[0-9]{2}\/[0-9]{2}?|[0-9]{2}\.[0-9]{2}\.[0-9]{2}?", text)
    res_parsed = {} # type : Dict[str, date]
    for date_str in res:
        try:
            parsed_date = parse(date_str, dayfirst = True)
            if abs(date.today().year - parsed_date.year) <= diff_years:
                res_parsed[date_str] = parsed_date
        except ValueError:
            pass
    return res_parsed

def flush_file(txt_out_filename):
    with open(txt_out_filename, "w") as out_file:
        out_file.write('')

def init_settings(shuffling : bool = False, img : np.ndarray = np.ndarray(0)) -> List[Setting]:
    # Initialize settings
    settings = []
    for preblur_level in (False, True):
        for dilate_iter_level in (10, 9, 8, 6):
            for bright_level in (0, 60, 100, 140):
                cur_setting = Setting(preblur = preblur_level, 
                                        dilate_iter = dilate_iter_level, 
                                        incr_bright = bright_level)
                if img.shape[0] > 0:
                    cur_setting.thresh = img
                settings.append(cur_setting)
    if shuffling:
        return sorted(random.sample(settings, len(settings)), key = lambda v : v._preblur)
        #return random.sample(settings, len(settings))
    return settings

def recognize_full_image(
        settings : List[Setting], 
        recognised_dates : OrderedDict[str, date], 
        data_dir : str,
        max_number_dates : int = 0
    ) -> None:
    recognition_log_file = f"{data_dir}/recognized_log.txt"
    for cur_setting in tqdm(settings):
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
        reductions_factors : Tuple[int, int] = (3, 4)
    ) -> None:
    settings = sorted(
        settings, 
        key = lambda v : v.recognized_text_len, 
        reverse = True
    )
    recognition_log_file = f"{data_dir}/recognized_tiles_log.txt"
    flush_file(recognition_log_file)
    for patch_reduction_factor in reductions_factors:
        for cur_setting in tqdm(settings):
        # # Image.fromarray(thresh).save(f"{data_dir}/thresh.png")
            patch_size = sorted(
                            [int(cur_setting.thresh.shape[0]/patch_reduction_factor), 
                                int(cur_setting.thresh.shape[1]/patch_reduction_factor)]
                            )
            for seed in range(2):
                for patch in extract_patches_2d(
                        cur_setting.thresh, 
                        patch_size = patch_size, 
                        max_patches = patch_reduction_factor ** 2, 
                        random_state = np.random.RandomState(seed)
                    ):
                    # Image.fromarray(patch).save(f"{data_dir}/patch_thresh.png")
                    text = my_ocr(recognition_log_file, patch)
                    if text:
                        recognised_dates.update(check_text(text))
                        if max_number_dates > 0 \
                            and len(recognised_dates) >= max_number_dates:
                            return

def filter_recognised_dates(recognised_dates : OrderedDict[str, date]) -> OrderedDict[str, date]:
    # if len(recognised_dates) == 2:
    #     return OrderedDict(sorted(recognised_dates.items(), key = lambda v : v[1]))
    # else:
    # Do filter dates
    recognised_dates_list = sorted(recognised_dates.items(), key = lambda v : v[1])
    dates_before_today = []
    dates_after_today = []
    for date_s, date_v in recognised_dates_list:
        if date_v < datetime.today():
            dates_before_today.append([date_s, date_v])
        else:
            dates_after_today.append([date_s, date_v])
    prod_dates = sorted(dates_before_today, key = lambda v : v[1])
    exp_dates = sorted(dates_after_today, key = lambda v : v[1])
    if len(prod_dates) > 0 and len(exp_dates) > 0:
        return OrderedDict([prod_dates[-1], exp_dates[0]])
    elif len(prod_dates) > 1:
        # Exp date before today
        return OrderedDict([prod_dates[-2], prod_dates[-1]])

def dates_recognition(img_path: str, data_dir : str, max_number_dates : int = 3) -> OrderedDict[str, date]:
    recognised_dates = OrderedDict() # type: OrderedDict
    if not path.exists(img_path):
        return recognised_dates
    # Read image
    img = cv2.imread(img_path)
    # Reduce resolution
    # while min(img.shape) > 800:
    #     img = cv2.pyrDown(img)
    # Rotate
    img, angle = descew_image(img)
    # Init several images views. Everyone will be used for OCR
    settings = init_settings(shuffling = True, img = img)
    # Try to recognize from full image
    recognize_full_image(
        settings = settings, 
        recognised_dates = recognised_dates, 
        data_dir = data_dir,
        max_number_dates = max_number_dates
    )
    print("\nrecognised_dates from full image:")
    print(recognised_dates)

    if len(recognised_dates) >= max_number_dates:
        recognised_dates = \
            filter_recognised_dates(recognised_dates = recognised_dates)
        print("\nfiltered recognised_dates:")
        print(recognised_dates)
        return recognised_dates
    elif len(recognised_dates) == 2:
        filtered_recognised_dates = \
            filter_recognised_dates(recognised_dates = recognised_dates)
        if len(filtered_recognised_dates) == 2:
            print("\nfiltered recognised_dates:")
            print(recognised_dates)
            return filtered_recognised_dates

    print("\nwill try to recognize from tiles image...")
    # Try to recognize from tiles image
    recognize_tiles_image(
        settings = settings, 
        recognised_dates = recognised_dates, 
        data_dir = data_dir,
        max_number_dates = max_number_dates
    )
    print("\nrecognised_dates:")
    print(recognised_dates)
    recognised_dates = \
        filter_recognised_dates(recognised_dates = recognised_dates)
    print("\nfiltered recognised_dates:")
    print(recognised_dates)
    return recognised_dates

def main():
    data_dir = "data/example/test_dates_recogn_1/"
    recognised_dates = dates_recognition(f"{data_dir}/IMG_3529.jpg", data_dir)

if __name__ == "__main__":
    st = time()
    main()
    end = time()
    print("Execution time: {:.6f} seconds".format(end - st))