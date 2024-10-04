from skimage.metrics import structural_similarity as ssim
import cv2
import numpy as np
import os
class ImageMatcher:
    def __init__(self, templates_dir):
        self.templates_dir = templates_dir
        self.templates = {}  # Initialize an empty dictionary to hold the templates
        self.load_templates()  # Load the templates when initializing the class

    def load_templates(self):
        """
        Loads all template images from the templates directory into memory.
        """
        try:
            for template_file in os.listdir(self.templates_dir):
                if template_file.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")):
                    template_path = os.path.join(self.templates_dir, template_file)
                    template_img = cv2.imread(template_path)
                    if template_img is not None:
                        # Extract an ID from the file name (assuming the file name has the template ID)
                        template_id = os.path.splitext(template_file)[0].split('_')[-1]
                        self.templates[template_id] = template_img
                        print(f"[DEBUG] Loaded template {template_file} with ID {template_id}")
                    else:
                        print(f"[DEBUG] Failed to load template image: {template_file}")
        except Exception as e:
            print(f"[DEBUG] Error loading templates: {e}")

    def compare_images(self, img1, img2):
        """
        Compares two images using Structural Similarity Index (SSIM) to determine if they match.
        """
        # Convert images to grayscale for comparison
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # Resize images to the same dimensions if necessary
        if gray1.shape != gray2.shape:
            gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))

        # Calculate SSIM between the two images
        score, _ = ssim(gray1, gray2, full=True)
        print(f"[DEBUG] SSIM score: {score}")

        # Define a threshold for similarity (1.0 means identical)
        threshold = 0.9
        return score >= threshold


    def match_images(self, img):
        """
        Matches the given image with the loaded templates and returns match_values and temp_img_id.
        """
        if not self.templates:
            print("[DEBUG] No templates loaded for matching.")
            return None, -1

        match_values = {}  # Dictionary to store match scores for each template

        # Loop over the templates and perform matching
        for template_id, template_img in self.templates.items():
            print(f"[DEBUG] Comparing with Template ID {template_id}")

            # Use the compare_images method to get the similarity score
            result = self.compare_images(img, template_img)
            print(f"[DEBUG] Matching with Template ID {template_id}: Similarity Score = {result}")
            
            # Store the match score for each template
            match_values[template_id] = result

        # Find the template with the highest similarity score
        best_match_id = max(match_values, key=match_values.get)
        best_match_value = match_values[best_match_id]

        # Return the highest similarity score and corresponding template ID
        print(f"[DEBUG] Best match found with Template ID: {best_match_id}, Score: {best_match_value}")
        return match_values, best_match_id
