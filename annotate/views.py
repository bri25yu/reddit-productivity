from django.shortcuts import render


def index(request):
    context = {
        "datapoint_id": 0,
        "submission_title": "Submission title",
        "comment_body": "Comment body",
    }
    return render(request, "annotate/index.html", context)
