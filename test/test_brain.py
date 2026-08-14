import numpy as np
from brain import Brain


brain = Brain(3, 2)


input_data = np.array([1, 2, 3])


output = brain.think(input_data)


print("Brain output:")
print(output)