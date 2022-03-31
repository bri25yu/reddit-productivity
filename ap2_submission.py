from pprint import pformat
import numpy as np

import pandas as pd


ADJUDICATED_INPUT_DATA_PATH = "data.csv"
ADJUDICATED_INPUT_LABELS_PATH = "adjudicated.csv"
ADJUDICATED_PATH = "adjudicated.txt"

ANNOTATION_PATHS = [
    ("Brian", "annotations_brian.csv"),
    ("Grace", "annotations_grace.csv"),
]
INDIVIDUAL_ANNOTATION_PATH = "individual_annotations.txt"

DATA_VALIDATION_PATH = "data_validation.txt"


def create_adjudicated():
    data = pd.read_csv(ADJUDICATED_INPUT_DATA_PATH, sep="\t")
    data = data.drop(columns=["submission_id", "comment_id", "annotation_split"])

    labels = pd.read_csv(ADJUDICATED_INPUT_LABELS_PATH, sep="\t")

    adjudicated = data.merge(labels, on="datapoint_id")

    adjudicated["text"] = adjudicated["submission_title"] \
        + " [SEP] " + adjudicated["comment_parent"] \
        + " [SEP] " + adjudicated["comment_body"]
    adjudicated["text"] = adjudicated["text"].replace([r"\n", r"\t"], " ", regex=True)
    adjudicated = adjudicated.drop(columns=["submission_title", "comment_parent", "comment_body"])
    adjudicated["adjudicated"] = "adjudicated"
    adjudicated = adjudicated.rename(columns={"score": "label"})

    adjudicated = adjudicated[["datapoint_id", "adjudicated", "label", "text"]]

    adjudicated.to_csv(ADJUDICATED_PATH, sep="\t", index=False, header=False)


def compile_individual():
    adjudicated = pd.read_csv(ADJUDICATED_PATH, sep="\t", names=["datapoint_id", "adjudicated", "label", "text"])
    data = pd.read_csv(ADJUDICATED_INPUT_DATA_PATH, sep="\t")
    evaluation_set = set(data["datapoint_id"][data["annotation_split"] == "evaluation"])
    compiled = pd.DataFrame(columns=["datapoint_id", "annotator_id", "label", "text"])

    datapoint_to_text_mappings = \
        {row["datapoint_id"]: row["text"] for _, row in adjudicated.iterrows()}

    for annotator_id, annotations_path in ANNOTATION_PATHS:
        annotations_df = pd.read_csv(annotations_path, sep="\t")
        for _, row in annotations_df.iterrows():
            if row["datapoint_id"] not in evaluation_set:
                continue

            compiled = compiled.append({
                "datapoint_id": row["datapoint_id"],
                "annotator_id": annotator_id,
                "label": row["score"],
                "text": datapoint_to_text_mappings[row["datapoint_id"]],
            }, ignore_index=True)

    compiled.to_csv(INDIVIDUAL_ANNOTATION_PATH, sep="\t", index=False, header=False)


if __name__ == "__main__":
    create_adjudicated()
    compile_individual()
