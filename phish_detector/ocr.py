from google.cloud import vision

from .api_counter import increment_vision


def get_wordlist_from_screen(img_path: str):
    client = vision.ImageAnnotatorClient()

    with open(img_path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)  # type: ignore
    increment_vision()
    wordlist = response.full_text_annotation.text.splitlines()
    return wordlist
