import cv2

def resize_image_cv2(input_image, new_size):
    try:
        original_height, original_width, _ = input_image.shape
        target_width = new_size["width"]
        target_height = new_size["height"]
        if (original_width, original_height) == (target_width, target_height):
            return input_image
        resized_image = cv2.resize(input_image, (target_width, target_height))
        return resized_image
    except Exception as e:
        print(f"Error resizing image: {e}")
        return None

def convert_to_grayscale(image):
    try:
        if len(image.shape) == 2:
            return image
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray_image
    except Exception as e:
        print(f"Error: {e}")
        return None

def read_and_crop_image(file_path, crop_coords):
    img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    x1, y1, x2, y2 = crop_coords
    return img[y1:y2, x1:x2]

def percentage_of_black_pixels(img):
    total_pixels = img.shape[0] * img.shape[1]
    black_pixels = (img == 0).sum()
    return (black_pixels / total_pixels) * 100.0
