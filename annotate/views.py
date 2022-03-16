import os
import pandas as pd
import random

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
        pass

    # Select random datapoint not already annotated
    datapoint_index = random.randint(0, len(data)-1)
    while pd.notna(annotations.iloc[datapoint_index]["score"]):
        datapoint_index = random.randint(0, len(data)-1)

    row = data.iloc[datapoint_index]

    context = {
        "datapoint_id": row["datapoint_id"],
        "submission_title": row["submission_title"],
        "comment_body": row["comment_body"],
    }
    return render(request, "annotate/index.html", context)
