import torch
from torch.utils.data import Dataset



class TextDataset(Dataset):

    def __init__(
        self,
        text,
        tokenizer,
        sequence_length=16
    ):

        self.tokens = tokenizer.encode(
            text
        )

        self.sequence_length = sequence_length




    def __len__(self):

        return len(self.tokens) - self.sequence_length




    def __getitem__(
        self,
        index
    ):

        inputs = self.tokens[
            index:index + self.sequence_length
        ]


        targets = self.tokens[
            index + 1:index + self.sequence_length + 1
        ]


        return (
            torch.tensor(
                inputs,
                dtype=torch.long
            ),

            torch.tensor(
                targets,
                dtype=torch.long
            )
        )