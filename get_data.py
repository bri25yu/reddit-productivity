import json
from django.db import NotSupportedError
import praw
import random
import pandas as pd
from tqdm import tqdm
import argparse


class DataHandler:
    CREDENTIALS_PATH = "credentials.json"
    RANDOM_SEED = 42

    DF_COLUMNS = [
        "datapoint_id",
        "submission_id",
        "comment_id",
        "submission_title",
        "comment_parent",
        "comment_body",
        "annotation_split",
    ]

    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument("--n_comments", default=1000)
        parser.add_argument("--n_submissions", default=100)
        parser.add_argument("--subreddit", default="worldnews")
        parser.add_argument("--data_save_path", default="data.csv")

        args = parser.parse_args()

        self.SUBREDDIT = args.subreddit
        self.N_COMMENTS = args.n_comments
        self.N_SUBMISSIONS = args.n_submissions
        self.DATA_SAVE_PATH = args.data_save_path

        self.COMMENTS_PER_SUBMISSION = self.N_COMMENTS // self.N_SUBMISSIONS

    def get_data(self):
        # Set up Reddit API
        credentials = self.get_reddit_credentials(self.CREDENTIALS_PATH)
        reddit = self.get_reddit_instance(credentials)

        # Get submissions
        subreddit = self.get_subreddit(reddit, self.SUBREDDIT)
        submissions = self.get_top_submissions(subreddit, self.N_SUBMISSIONS)

        # Get comments in df
        df = self.get_comments(submissions)

        # Assign rows to exploration or evaluation set
        df = self.assign_split(df)

    @staticmethod
    def get_reddit_credentials(path: str) -> dict:
        return json.load(open(path))

    @staticmethod
    def get_reddit_instance(credentials: dict) -> praw.Reddit:
        return praw.Reddit(**credentials)

    @staticmethod
    def get_subreddit(
        reddit: praw.Reddit, subreddit_name: str
    ) -> praw.models.Subreddit:
        return reddit.subreddit(subreddit_name)

    @staticmethod
    def get_top_submissions(
        subreddit: praw.models.Subreddit, n: int
    ) -> praw.models.listing.generator.ListingGenerator:
        return subreddit.top(limit=n)

    @staticmethod
    def get_random_comment(
        comments: praw.models.comment_forest.CommentForest,
        seen: set,
    ) -> dict:
        while (comment := comments[random.randint(0, len(comments) - 1)]) \
            and (replies := comment.replies) \
            and random.randint(0, 1) == 1:
            comments = replies

        comment_missing = comment.body in ["[removed]", "[deleted]"]
        if comment_missing or comment.id in seen:
            return None

        if comment.parent_id.startswith("t3_"):  # Parent is a submission
            comment_parent = comment.parent().title
        elif comment.parent_id.startswith("t1_"):  # Parent is another comment
            comment_parent = comment.parent().body
        else:
            raise NotSupportedError(f"Unknown parent type: {comment.parent_id}")

        return {
            "comment_id": comment.id,
            "comment_body": comment.body,
            "comment_parent": comment_parent,
        }

    def get_comments(
        self, submissions: praw.models.listing.generator.ListingGenerator
    ) -> pd.DataFrame:
        random.seed(
            self.RANDOM_SEED
        )  # Set random seed for deterministic random selection
        progress_bar = tqdm(range(self.N_COMMENTS), desc="Getting data")
        df = pd.DataFrame(columns=self.DF_COLUMNS)

        for submission in submissions:
            comments = submission.comments
            comments.replace_more(limit=0)

            rows, seen = [], set()
            while len(rows) < self.COMMENTS_PER_SUBMISSION:
                row = self.get_random_comment(comments, seen)
                if row is None:
                    continue

                rows.append(
                    {
                        "datapoint_id": len(df) + len(rows),
                        "submission_id": submission.id,
                        "submission_title": submission.title,
                        **row,
                    }
                )
                progress_bar.update(1)

            df = df.append(rows, ignore_index=True)
            df.to_csv(
                self.DATA_SAVE_PATH, sep="\t", index=False
            )  # Save csv periodically

        return df

    def assign_split(self, df: pd.DataFrame) -> pd.DataFrame:
        random.seed(self.RANDOM_SEED)

        exploration_indices = set(random.sample(range(len(df)), k=len(df) // 2))
        for i in range(len(df)):
            split = "exploration" if i in exploration_indices else "evaluation"
            df.at[i, "annotation_split"] = split

        df.to_csv(self.DATA_SAVE_PATH, sep="\t", index=False)

        return df


if __name__ == "__main__":
    d = DataHandler()
    d.get_data()
