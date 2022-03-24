import os
import pandas as pd
import random
from markdown import markdown
from typing import Tuple

from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView


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


def index(request):
    if request.method == "POST":
        request.session["annotation_split"] = request.POST["annotation_split"]
        return redirect("annotate")

    return render(request, "annotate/index.html")


class AnnotateView(TemplateView):

    template_name = "annotate/annotate.html"

    def dispatch(self, request, *args, **kwargs):
        if "annotation_split" not in request.session:
            return redirect("index")

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        datapoint_id = int(request.POST["datapoint_id"])
        score = request.POST["score"]

        _, annotations = self._get_data_annotations()

        datapoint_index = self._datapoint_id_to_index(annotations, datapoint_id)
        annotations.at[datapoint_index, "score"] = score
        annotations.to_csv(ANNOTATION_OUTPUT_PATH, sep="\t", index=False)

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        annotation_split = self.request.session["annotation_split"]
        data, annotations = self._get_data_annotations()

        data_split, annotations_split, split_ids = self._get_data_splits(
            data, annotations, annotation_split
        )
        row = self._get_next_row(data_split, annotations_split)

        return {
            "datapoint_id": row["datapoint_id"],
            "submission_title": markdown(row["submission_title"]),
            "comment_parent": markdown(row["comment_parent"]),
            "comment_body": markdown(row["comment_body"]),
            "annotation_split": annotation_split,
            "annotations_finished": annotations_split["score"].notna().sum(),
            "annotation_total": len(data_split),
            "labels": LABELS,
        }

    @staticmethod
    def _get_data_annotations() -> tuple:
        return data, annotations

    @staticmethod
    def _get_data_splits(
        data: pd.DataFrame,
        annotations: pd.DataFrame,
        annotation_split: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame, set]:
        if annotation_split == "full":
            return data, annotations, set(range(len(data)))

        split_ids = set(
            data["datapoint_id"][data["annotation_split"] == annotation_split].values
        )

        data_split = data[data["datapoint_id"].isin(split_ids)].reset_index(drop=True)
        annotations_split = annotations[
            annotations["datapoint_id"].isin(split_ids)
        ].reset_index(drop=True)

        return data_split, annotations_split, split_ids

    @staticmethod
    def _get_next_row(data: pd.DataFrame, annotations: pd.DataFrame) -> pd.DataFrame:
        datapoint_index = random.randint(0, len(data) - 1)
        while pd.notna(annotations.iloc[datapoint_index]["score"]):
            datapoint_index = random.randint(0, len(data) - 1)

        return data.iloc[datapoint_index]

    @staticmethod
    def _datapoint_id_to_index(df: pd.DataFrame, datapoint_id: int) -> int:
        return df[df["datapoint_id"] == datapoint_id].index[0]
