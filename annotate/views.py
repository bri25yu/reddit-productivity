import os
import pandas as pd
import random
from markdown import markdown
from typing import Tuple

from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.core.paginator import Paginator


LABELS = [
    "Arbitrate",
    "Inquire",
    "Argue",
    "Summarize",
    "Inform",
    "Connect",
    "Rhetorical",
]


ANNOTATION_OUTPUT_PATH = "annotations.csv"
ANNOTATIONS_DF_COLUMNS = ["datapoint_id", "score"]


def provision() -> Tuple[pd.DataFrame, pd.DataFrame, list]:
    data = pd.read_csv("data.csv", sep="\t")
    if not os.path.exists(ANNOTATION_OUTPUT_PATH):
        annotations = pd.DataFrame(columns=ANNOTATIONS_DF_COLUMNS)
        annotations["datapoint_id"] = data["datapoint_id"]
        annotations.to_csv(ANNOTATION_OUTPUT_PATH, sep="\t", index=False)
    else:
        annotations = pd.read_csv(ANNOTATION_OUTPUT_PATH, sep="\t")

    random.seed(42)
    annotation_ordering = list(range(len(data)))
    random.shuffle(annotation_ordering)

    return data, annotations, annotation_ordering

data, annotations, annotation_ordering = provision()


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

        annotations = self._get_data_annotations()[1]

        datapoint_index = self._datapoint_id_to_index(annotations, datapoint_id)
        annotations.at[datapoint_index, "score"] = score
        annotations.to_csv(ANNOTATION_OUTPUT_PATH, sep="\t", index=False)

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        annotation_split = self.request.session["annotation_split"]
        data, annotations, annotation_ordering = self._get_data_annotations()

        data_split, annotations_split, annotation_ordering_split = self._get_data_splits(
            data, annotations, annotation_ordering, annotation_split
        )
        row = self._get_next_row(data_split, annotations_split, annotation_ordering_split)

        comments = [
            {
                "submission_title": markdown(row["submission_title"]),
                "comment_parent": markdown(row["comment_parent"]),
                "comment_body": markdown(row["comment_body"]),
            }
        ]

        return {
            "comments": comments,
            "datapoint_id": row["datapoint_id"],
            "annotation_split": annotation_split,
            "annotations_finished": annotations_split["score"].notna().sum(),
            "annotation_total": len(data_split),
            "labels": LABELS,
        }

    @staticmethod
    def _get_data_annotations() -> Tuple[pd.DataFrame, pd.DataFrame, list]:
        return data, annotations, annotation_ordering

    @staticmethod
    def _get_data_splits(
        data: pd.DataFrame,
        annotations: pd.DataFrame,
        annotation_ordering: list,
        annotation_split: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame, list]:
        if annotation_split == "full":
            return data, annotations, set(range(len(data)))

        split_ids = set(
            data["datapoint_id"][data["annotation_split"] == annotation_split].values
        )

        data_split = data[data["datapoint_id"].isin(split_ids)].reset_index(drop=True)
        annotations_split = annotations[
            annotations["datapoint_id"].isin(split_ids)
        ].reset_index(drop=True)

        annotation_ordering_split = [i for i in annotation_ordering if i in split_ids]

        return data_split, annotations_split, annotation_ordering_split

    def _get_next_row(
        self,
        data: pd.DataFrame,
        annotations: pd.DataFrame,
        ordering: list,
    ) -> pd.DataFrame:
        for datapoint_id in ordering:
            datapoint_index = self._datapoint_id_to_index(annotations, datapoint_id)
            if pd.isna(annotations.iloc[datapoint_index]["score"]):
                break

        return data.iloc[self._datapoint_id_to_index(data, datapoint_id)]

    @staticmethod
    def _datapoint_id_to_index(df: pd.DataFrame, datapoint_id: int) -> int:
        return df[df["datapoint_id"] == datapoint_id].index[0]


def aggregate(request):
    comments = []
    for i in range(len(annotations)):
        if pd.isna(annotations.iloc[i]["score"]):
            continue

        datapoint_id = annotations.iloc[i]["datapoint_id"]
        datapoint_index = AnnotateView._datapoint_id_to_index(data, datapoint_id)
        row = data.iloc[datapoint_index]

        comments.append({
            "submission_title": markdown(row["submission_title"]),
            "comment_parent": markdown(row["comment_parent"]),
            "comment_body": markdown(row["comment_body"]),
            "annotation_split": row["annotation_split"],
            "score_given": annotations.iloc[i]["score"],
        })

    paginator = Paginator(comments, 1) # Show 25 contacts per page.

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"comments": page_obj, "page_obj": page_obj}
    return render(request, "annotate/aggregate.html", context)
