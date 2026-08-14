import numpy as np

from attention import Attention


attention = Attention(3)


query = np.array([1, 0, 1])


keys = [
    np.array([1, 0, 0]),
    np.array([0, 1, 0]),
    np.array([1, 1, 1])
]


values = [
    np.array([5, 0, 0]),
    np.array([0, 5, 0]),
    np.array([0, 0, 5])
]


result = attention.calculate(
    query,
    keys,
    values
)


print(result)