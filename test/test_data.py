from dataset import Dataset


data = Dataset(
    "data"
)


print(
    "Loaded characters:",
    len(data.text)
)