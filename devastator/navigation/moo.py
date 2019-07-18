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
                assert col < self.n , "you are a disaster"
            self.transform_matrix[row+observed_rows][col] = 1
            col += 1

if __name__ == "__main__":

    def magic(n):
        n = int(n)
        if n < 3:
            raise ValueError("Size must be at least 3")
        if n % 2 == 1:
            p = np.arange(1, n+1)
            return n*np.mod(p[:, None] + p - (n+3)//2, n) + np.mod(p[:, None] + 2*p-2, n) + 1
        elif n % 4 == 0:
            J = np.mod(np.arange(1, n+1), 4) // 2
            K = J[:, None] == J
            M = np.arange(1, n*n+1, n)[:, None] + np.arange(n)
            M[K] = n*n + 1 - M[K]
        else:
            p = n//2
            M = magic(p)
            M = np.block([[M, M+2*p*p], [M+3*p*p, M+p*p]])
            i = np.arange(p)
            k = (n-2)//4
            j = np.concatenate((np.arange(k), np.arange(n-k+1, n)))
            M[np.ix_(np.concatenate((i, i+p)), j)] = M[np.ix_(np.concatenate((i+p, i)), j)]
            M[np.ix_([k, k+p], [0, k])] = M[np.ix_([k+p, k], [0, k])]
        return M 
    
    params = {
        'A' : magic(4),
        'idx_to_observe' : [1, 3]
    }
    m = magic(4)
    obs = MOO(params)
    print(m)
    tm = obs.transform_matrix @ m
    print(tm)
    ttm = np.transpose(obs.transform_matrix) @ tm
    print(ttm)
    print(ttm == m)


