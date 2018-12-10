from PIL import Image,ImageEnhance
import pytesseract

def GetCode(path):
    im = Image.open(path)

    im=im.convert('L')
    im=ImageEnhance.Contrast(im)
    im=im.enhance(3)
    img2 = Image.new('RGB', (150, 60), (255, 255, 255))
    img2.paste(im.copy(), (25, 10))
    
    return pytesseract.image_to_string(img2)