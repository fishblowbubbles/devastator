import numpy as np
# import control

### PARAMS ###


class MOO(object):
    '''
    Minimum Order Observer
    '''
    def __init__(self, params):
        self.idx_to_observe = params.get('idx_to_observe', [0])
        self.A = params['A']
        self.n = self.A.shape[0]
        assert self.n is self.A.shape[1], "Matrix A is not square!"

        # create transformation matrix to choose states to observe
        self.transform_matrix = np.zeros((self.n, self.n))
        for i, j in enumerate(self.idx_to_observe):
            self.transform_matrix[i][j] = 1
        col = 0
        observed_rows = len(self.idx_to_observe)
        for row in range(self.n-observed_rows):
            while col in self.idx_to_observe:
                col += 1
                assert col < self.n , "you are a disaster coder"
            self.transform_matrix[row+observed_rows][col] = 1
            col += 1

        self._A = self.transform_matrix @ self.A #

if __name__ == "__main__":
    pass