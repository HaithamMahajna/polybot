from pathlib import Path
from matplotlib.image import imread, imsave

def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


class Img:

    def __init__(self, path):
        """
        Do not change the constructor implementation
        """
        self.path = Path(path)
        self.data = rgb2gray(imread(path)).tolist()

    def save_img(self):
        """
        Do not change the below implementation
        """
        new_path = self.path.with_name(self.path.stem + '_filtered' + self.path.suffix)
        imsave(new_path, self.data, cmap='gray')
        return new_path

    def blur(self, blur_level=16):

        height = len(self.data)
        width = len(self.data[0])
        filter_sum = blur_level ** 2

        result = []
        for i in range(height - blur_level + 1):
            row_result = []
            for j in range(width - blur_level + 1):
                sub_matrix = [row[j:j + blur_level] for row in self.data[i:i + blur_level]]
                average = sum(sum(sub_row) for sub_row in sub_matrix) // filter_sum
                row_result.append(average)
            result.append(row_result)

        self.data = result

    def contour(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(abs(row[j-1] - row[j]))

            self.data[i] = res

    def rotate(self):
        rows = len(self.data)
        cols = len(self.data[0])

        rotated = []
        for col in range(cols):
            new_row = []
            for row in reversed(range(rows)):
                new_row.append(self.data[row][col])
            rotated.append(new_row)

        self.data = rotated



    def salt_n_pepper(self):
        import random
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                rnd = random.random()  # Random float between 0 and 1
                if rnd < 0.2:
                    self.data[i][j] = 255  # Salt
                elif rnd > 0.8:
                    self.data[i][j] = 0  # Pepper
                # Otherwise, leave pixel unchanged

    def concat(self, other_img, direction='horizontal'):

        if direction == 'horizontal':

            if len(self.data) != len(other_img.data):
                raise ValueError("Images must have the same number of rows to concatenate horizontally.")

            concatenated = []
            for row_self, row_other in zip(self.data, other_img.data):
                concatenated.append(row_self + row_other)
            self.data = concatenated

        elif direction == 'vertical':

            if len(self.data[0]) != len(other_img.data[0]):
                raise ValueError("Images must have the same number of columns to concatenate vertically.")

            self.data = self.data + other_img.data

        else:
            raise ValueError("Direction must be 'horizontal' or 'vertical'.")

    def segment(self):

        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                if self.data[i][j] > 100:
                    self.data[i][j] = 255
                else:
                    self.data[i][j] = 0

