import pytesseract
from PIL import Image, ImageEnhance


def autocaptcha(path):
    """Auto identify captcha in path.

    Use pytesseract to identify captcha.

    Args:
        path: string, image path.

    Returns:
        string, OCR identified code.
    """
    im = Image.open(path)

    im = im.convert('L')
    im = ImageEnhance.Contrast(im)
    im = im.enhance(3)
    img2 = Image.new('RGB', (150, 60), (255, 255, 255))
    img2.paste(im.copy(), (25, 10))

    # TODO: add auto environment detect
    return pytesseract.image_to_string(img2)
