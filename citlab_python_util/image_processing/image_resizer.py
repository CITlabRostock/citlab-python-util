import os

import cv2
import numpy as np

from citlab_python_util.io.file_loader import load_image
from citlab_python_util.io.file_loader import load_list_file
from citlab_python_util.logging import custom_logging

logger = custom_logging.setup_custom_logger("ImageResizer", "info")


class ImageResizer:
    def __init__(self, path_to_image_list, max_height=0, max_width=0, scaling_factor=1.0):
        self.image_path_list = load_list_file(path_to_image_list)
        self.image_list = [load_image(image_path, "pil", mode="L") for image_path in self.image_path_list]
        self.image_resolutions = [pil_image.size for pil_image in self.image_list]  # (width, height) resolutions
        self.max_width = max(0, max_width)
        self.max_height = max(0, max_height)
        if (self.max_height, self.max_width) is not (0, 0):
            self.scaling_factors = self.calculate_scaling_factors_from_max_resolution()
        else:
            self.scaling_factors = [scaling_factor] * len(self.image_list)
        self.resized_images = []

    def set_max_resolution(self, max_height=0, max_width=0):
        self.max_height = max_height
        self.max_width = max_width
        self.scaling_factors = self.calculate_scaling_factors_from_max_resolution()

    def save_resized_images(self, save_folder):
        if len(self.resized_images) == 0:
            self.resize_images()

        for i, (image_path, resized_image) in enumerate(zip(self.image_path_list, self.resized_images)):
            image_name = os.path.basename(image_path)
            save_path = os.path.join(save_folder, image_name)

            logger.debug(f"Save image in {save_path}")
            logger.debug(f"Scaling factor: {self.scaling_factors[i]}")
            logger.debug(f"Max_height: {self.max_height}")
            logger.debug(f"Max_width: {self.max_width}")

            cv2.imwrite(save_path, resized_image)

    def calculate_scaling_factors_from_max_resolution(self):
        if (self.max_height, self.max_width) == (0, 0):
            logger.debug("No max resolution given, do nothing...")
            return [1.0] * len(self.image_path_list)

        if self.max_height == 0:
            return [min(1.0, self.max_width / img_res[0]) for img_res in self.image_resolutions]
        elif self.max_width == 0:
            return [min(1.0, self.max_height / img_res[1]) for img_res in self.image_resolutions]
        else:
            return [min(1.0, max(self.max_width / img_res[0], self.max_height / img_res[1])) for img_res
                    in self.image_resolutions]

    def resize_images(self):
        self.resized_images = [self.resize_image(pil_image, sc) for pil_image, sc in
                               zip(self.image_list, self.scaling_factors)]

    def resize_image(self, pil_image, scaling_factor):
        image = np.array(pil_image, np.uint8)
        if scaling_factor < 1:
            return cv2.resize(image, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
        elif scaling_factor > 1:
            return cv2.resize(image, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_CUBIC)
        else:
            return image


if __name__ == '__main__':
    max_heights = [i for i in range(1000, 3000, 500)]
    image_resizer = ImageResizer(
        path_to_image_list="/home/max/data/la/racetrack_onb_corrected_baselines_no_tifs/racetrack_onb_corrected_baselines.lst")
    for max_height in max_heights:
        image_resizer.set_max_resolution(max_height=max_height)
        save_folder = save_folder = "/home/max/newspaper_different_heights/" + str(max_height)
        if not os.path.exists(save_folder):
            os.mkdir(save_folder)
        image_resizer.resize_images()
        image_resizer.save_resized_images(save_folder)
