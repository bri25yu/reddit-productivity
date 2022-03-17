import os
import pandas as pd
import random
from markdown import markdown

from django.shortcuts import render


ANNOTATION_OUTPUT_PATH = "annotations.csv"
ANNOTATIONS_DF_COLUMNS = ["datapoint_id", "score"]

data = pd.read_csv("data.csv", sep="\t")
if not os.path.exists(ANNOTATION_OUTPUT_PATH):
    annotations = pd.DataFrame(columns=ANNOTATIONS_DF_COLUMNS)
    annotations["datapoint_id"] = data["datapoint_id"]
    annotations.to_csv(ANNOTATION_OUTPUT_PATH, sep="\t", index=False)
else:
    annotations = pd.read_csv(ANNOTATION_OUTPUT_PATH, sep="\t")


def index(request):
    if request.method == "POST":
        datapoint_index = int(request.POST["datapoint_index"])
        score = int("productive" in request.POST)

        annotations.at[datapoint_index, "score"] = score
        annotations.to_csv(ANNOTATION_OUTPUT_PATH, sep="\t", index=False)

    # Select random datapoint not already annotated
    datapoint_index = random.randint(0, len(data)-1)
    while pd.notna(annotations.iloc[datapoint_index]["score"]):
        datapoint_index = random.randint(0, len(data)-1)

    row = data.iloc[datapoint_index]

    context = {
        "datapoint_index": datapoint_index,
        "submission_title": markdown(row["submission_title"]),
        "comment_body": markdown(row["comment_body"]),
        "annotations_finished": annotations["score"].notna().sum(),
        "annotation_total": len(data),
    }
    return render(request, "annotate/index.html", context)
