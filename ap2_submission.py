from pprint import pformat

from collections import Counter
import numpy as np

import pandas as pd


ADJUDICATED_INPUT_DATA_PATH = "data.csv"
ADJUDICATED_INPUT_LABELS_PATH = ""
ADJUDICATED_PATH = "adjudicated_data.txt"

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


class DataValidation:
    def __init__(self):
        open(DATA_VALIDATION_PATH, "w").writelines([])

        self.check_file(ADJUDICATED_PATH, 1000)
        annotation_triples = self.check_individual_file(INDIVIDUAL_ANNOTATION_PATH)
        self.fleiss(annotation_triples)

    @staticmethod
    def check_file(filename, min_count):
        annotator_triples={}
        annos_by_data_id={}
        with open(filename, encoding="utf-8") as file:
            for idx, line in enumerate(file):
                cols=line.rstrip().split("\t")
                assert len(cols) == 4, "%s does not have 4 columns" % pformat(cols)
                assert len(cols[3]) > 0, "text #%s# in row %s is empty" % (cols[3], idx)
                assert len(cols[2]) > 0, "label #%s# in row %s is empty" % (cols[2], idx)
                annotator_triples[cols[1], cols[0], cols[2]]=1
                annos_by_data_id[cols[0]]=1
            assert len(annos_by_data_id) >= min_count, "You must have at least %s labels; this file only has %s" % (min_count, len(annos_by_data_id))

        open(DATA_VALIDATION_PATH, "a").writelines([
            "This file looks to be in the correct format; %s data points\n\n" % len(annos_by_data_id),
        ])

    @staticmethod
    def check_individual_file(filename):
        annotator_triples={}
        annos_by_data_id={}
        annos_by_annotator={}
        labels={}
        with open(filename, encoding="utf-8") as file:
            count=0
            for idx, line in enumerate(file):
                cols=line.rstrip().split("\t")
                data_id=cols[0]
                anno_id=cols[1]
                label=cols[2]

                assert len(cols) == 4, "%s does not have 4 columns" % pformat(cols)
                assert len(cols[3]) > 0, "text #%s# in row %s is empty" % (cols[3], idx)
                assert len(label) > 0, "label #%s# in row %s is empty" % (cols[2], idx)
                count+=1

                annotator_triples[anno_id, data_id, label]=1

                if data_id not in annos_by_data_id:
                    annos_by_data_id[data_id]={}
                annos_by_data_id[data_id][anno_id]=1

                if anno_id not in annos_by_annotator:
                    annos_by_annotator[anno_id]={}
                annos_by_annotator[anno_id][data_id]=1

                if label not in labels:
                    labels[label]=0
                labels[label]+=1    

        assert len(annos_by_data_id) >= 500, "You must have labels for at least 500 documents; this file only has %s" % (len(annos_by_data_id))

        for data_id in annos_by_data_id:
            assert len(annos_by_data_id[data_id]) == 2, "Each data point must have two annotations; data id %s does not" % data_id

        
        f = open(DATA_VALIDATION_PATH, "a")
        to_write = []

        to_write.append("Annotators:\n\n")
        for anno_id in annos_by_annotator:
            to_write.append("%s: %s\n" % (anno_id, len(annos_by_annotator[anno_id])))

        to_write.append("\nLabels:\n\n")
        for label in labels:
            to_write.append("%s: %s\n" % (label, labels[label]))

        to_write.append("\nThis file looks to be in the correct format; %s data points; %s annotations\n" % (len(annos_by_data_id), len(annotator_triples)))

        f.writelines(to_write)
        f.close()

        return list(annotator_triples.keys())

    @staticmethod
    def fleiss(annotation_triples):
        cats={}
        items={}
        uid_counts=Counter()
        uid_id={}
        aid_counts=Counter()

        # get label categories and unique data points
        for aid, uid, label in annotation_triples:
            if label not in cats:
                cats[label]=len(cats)
                if uid not in uid_id:
                    uid_id[uid]=len(uid_id)

                uid_counts[uid]+=1

        ncats=len(cats)
        ps=np.zeros(ncats)

        data = []

        for aid, uid, label in annotation_triples:

            if uid not in items:
                items[uid]=np.zeros(ncats)

            items[uid][cats[label]]+=1
            ps[cats[label]]+=1

        ps/=np.sum(ps)

        expected=0.
        for i in range(ncats):
            expected+=ps[i]*ps[i]

        agreements=[]
        for item in items:
            total=np.sum(items[item])
            assert total >= 2, "every data point must have at least two annotations; this one has %s" % (total)
            summ=0

            for i in range(ncats):
                summ+=items[item][i]*(items[item][i]-1)
            summ/=(total*(total-1))

            agreements.append(summ)

        observed=np.mean(agreements)
        open(DATA_VALIDATION_PATH, "a").writelines([
            "Observed: %.3f\n" % (observed),
            "Expected: %.3f\n" % (expected),
            "Fleiss' kappa: %.3f\n" % ((observed-expected)/(1-expected)),
        ])


if __name__ == "__main__":
    create_adjudicated()
    compile_individual()
    DataValidation()
