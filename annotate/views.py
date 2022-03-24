import os
import pandas as pd
import random
from markdown import markdown

from django.shortcuts import render, redirect


LABELS = [
    "Arbitrate",
    "Vouch",
    "Meme",
    "Opinion",
    "Informative",
]


ANNOTATION_OUTPUT_PATH = "annotations.csv"
ANNOTATIONS_DF_COLUMNS = ["datapoint_id", "score"]

data = pd.read_csv("data.csv", sep="\t")
if not os.path.exists(ANNOTATION_OUTPUT_PATH):
    annotations = pd.DataFrame(columns=ANNOTATIONS_DF_COLUMNS)
    annotations["datapoint_id"] = data["datapoint_id"]
    annotations.to_csv(ANNOTATION_OUTPUT_PATH, sep="\t", index=False)
else:
    annotations = pd.read_csv(ANNOTATION_OUTPUT_PATH, sep="\t")


def get_data_annotations():
    return data, annotations


def datapoint_id_to_index(df: pd.DataFrame, datapoint_id: int) -> int:
    return df[df["datapoint_id"] == datapoint_id].index[0]


def index(request):
    if request.method == "POST":
        request.session["annotation_split"] = request.POST["annotation_split"]
        return redirect("annotate")

    return render(request, "annotate/index.html")


def annotate(request):
    if "annotation_split" not in request.session:
        return redirect("index")

    annotation_split = request.session["annotation_split"]
    data, annotations = get_data_annotations()

    if request.method == "POST":
        datapoint_id = int(request.POST["datapoint_id"])
        score = request.POST["score"]

        datapoint_index = datapoint_id_to_index(annotations, datapoint_id)
        annotations.at[datapoint_index, "score"] = score
        annotations.to_csv(ANNOTATION_OUTPUT_PATH, sep="\t", index=False)

    if annotation_split != "full":
        split_ids = set(
            data["datapoint_id"][data["annotation_split"] == annotation_split].values
        )

        data = data[data["datapoint_id"].isin(split_ids)].reset_index(drop=True)
        annotations = annotations[
            annotations["datapoint_id"].isin(split_ids)
        ].reset_index(drop=True)

    # Select random datapoint not already annotated
    datapoint_index = random.randint(0, len(data) - 1)
    while pd.notna(annotations.iloc[datapoint_index]["score"]):
        datapoint_index = random.randint(0, len(data) - 1)

    row = data.iloc[datapoint_index]

    context = {
        "datapoint_id": row["datapoint_id"],
        "submission_title": markdown(row["submission_title"]),
        "comment_parent": markdown(row["comment_parent"]),
        "comment_body": markdown(row["comment_body"]),
        "annotation_split": annotation_split,
        "annotations_finished": annotations["score"].notna().sum(),
        "annotation_total": len(data),
        "labels": LABELS,
    }
    return render(request, "annotate/annotate.html", context)
