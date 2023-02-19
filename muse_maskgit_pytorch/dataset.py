"""
Author: Isamu Isozaki (isamu.website@gmail.com)
Description: description
Created:  2023-02-18T03:59:45.810Z
Modified: !date!
Modified By: modifier
"""
from torch.utils.data import Dataset
import torchvision.transforms as T
from PIL import Image, ImageFile
from pathlib import Path
from muse_maskgit_pytorch.t5 import MAX_LENGTH
import datasets
import random
ImageFile.LOAD_TRUNCATED_IMAGES = True


class ImageDataset(Dataset):
    def __init__(self, folder, image_size, exts=["jpg", "jpeg", "png"]):
        super().__init__()
        self.folder = folder
        self.image_size = image_size
        self.paths = [p for ext in exts for p in Path(f"{folder}").glob(f"**/*.{ext}")]

        print(f"{len(self.paths)} training samples found at {folder}")

        self.transform = T.Compose(
            [
                T.Lambda(lambda img: img.convert("RGB") if img.mode != "RGB" else img),
                T.Resize(image_size),
                T.RandomHorizontalFlip(),
                T.CenterCrop(image_size),
                T.ToTensor(),
            ]
        )

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, index):
        path = self.paths[index]
        img = Image.open(path)
        return self.transform(img)
class ImageTextDataset(Dataset):
    def __init__(self, dataset, image_size, tokenizer, image_column="image", caption_column="caption"):
        super().__init__()
        self.image_column = image_column
        self.caption_column = caption_column
        self.tokenizer = tokenizer
        self.dataset = dataset
        self.transform = T.Compose(
            [
                T.Lambda(lambda img: img.convert("RGB") if img.mode != "RGB" else img),
                T.Resize(image_size),
                T.RandomHorizontalFlip(),
                T.CenterCrop(image_size),
                T.ToTensor(),
            ]
        )
    def __getitem__(self, index):
        image= self.dataset[index][self.image_column]
        if self.caption_column == None:
            text = ""
        else:
            text = self.dataset[index][self.caption_column]
        encoded = self.tokenizer.batch_encode_plus(
            [text],
            return_tensors="pt",
            padding="longest",
            max_length=MAX_LENGTH,
            truncation=True,
        )

        input_ids = encoded.input_ids
        attn_mask = encoded.attention_mask
        return self.transform(image), input_ids, attn_mask

def get_dataset_from_dataroot(data_root, args):
    image_paths = list(Path(data_root).rglob("*.[jJ][pP][gG]"))
    random.shuffle(image_paths)
    data_dict = {args.image_column: [], args.caption_column: []}
    for image_path in image_paths:
        image = Image.open(image_path)
        if not image.mode == "RGB":
            image = image.convert("RGB")
        data_dict[args.image_column].append(image)
        data_dict[args.caption_column].append(None)
    return datasets.Dataset.from_dict(data_dict)