import os

import torch
from PIL import Image
from torch.nn import Softmax
from torchvision import models, transforms


class GunClassifier(object):
    def __init__(self, state_dict = 'resnet18_loss_1.056413.pt'):
        """
        :param state_dict: path to the saved state of the model (ResNet18)
        """
        self.index2label = {0: 'CZ P-07',
                            1: 'FN_MAG',
                            2: 'Glock G23',
                            3: 'Glock 19',
                            4: 'M16',
                            5: 'M249 SAW',
                            6: 'MP5',
                            7: 'P226',
                            8: 'SAR21',
                            9: 'Sphinx 3000',
                            10: 'Taurus M85',
                            11: 'Ultimax 100'}
        
        self.model = models.resnet18()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        if state_dict and os.path.exists(state_dict):
            self.model.load_state_dict(torch.load(state_dict, map_location = self.device))

    @staticmethod
    def load_image(image, path = True):
        """
        :param image: str if path else PIL.Image
        :param path: if image input is a path to the image
        """
        img_extensions = ('.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif', '.tiff', '.webp')

        if path:
            assert image.lower().endswith(img_extensions), 'supported extensions are:' + ', '.join(img_extensions)
            # open path as file to avoid ResourceWarning (https://github.com/python-pillow/Pillow/issues/835)
            with open(image, 'rb') as f:
                img = Image.open(f)
                return img.convert('RGB')

        return image
    
    def inference(self, image, path = True):
        img = self.load_image(image, path)
        
        self.model.eval()
        print('predicting')
        
        with torch.no_grad():
            image_tensor = transforms.ToTensor()(img).unsqueeze_(0).to(self.device)
            output = self.model(image_tensor)
            softmax_output = Softmax(dim = 1)(output)
            confidence, predicted_index = torch.max(softmax_output, 1)
            predicted = self.index2label[int(predicted_index[0])]
            
        if confidence < .5:
            predicted = 'unknown firearm'
            
        return float(confidence), predicted
    
    
if __name__ == '__main__':
    gun_classifier = GunClassifier(state_dict = 'resnet18_loss_1.056413.pt')
    print(gun_classifier.inference(image = 'Guns/Glock19/Glock19_21.jpg', path = True))
