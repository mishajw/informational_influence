# pylint: disable=missing-docstring

from pathlib import Path
from typing import List, NamedTuple
import argparse

from praw import Reddit

from . import cache


class Comment(NamedTuple):
    text: str
    votes: List[int]


class Post(NamedTuple):
    post_id: str


class Semantics(NamedTuple):
    happiness: float
    sadness: float


def main() -> None:
    parser = argparse.ArgumentParser("informational_influence")
    parser.add_argument("--client-id", type=str, required=True)
    parser.add_argument("--client-secret", type=str, required=True)
    parser.add_argument("--output", type=str, default="output")

    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_dir():
        output.mkdir()

    reddit = create_reddit(args.client_id, args.client_secret)
    posts = get_posts.with_cache(output / "posts", reddit)
    comments = dict(
        (
            p,
            get_comments.with_cache(
                output / f"comments-{p.post_id}", reddit, p
            ),
        )
        for p in posts
    )
    semantics = dict(
        (p, [get_semantics(c) for c in comments[p]]) for p in posts
    )

    print("posts", posts)
    print("comments", comments)
    print("semantics", semantics)


def create_reddit(client_id: str, client_secret: str) -> Reddit:
    return Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent="informational_influence",
    )


@cache
def get_posts(reddit: Reddit) -> List[Post]:
    return [Post(post.id) for post in reddit.subreddit("news").new(limit=10)]


@cache
def get_comments(reddit: Reddit, post: Post) -> List[Comment]:
    submission = reddit.submission(post.post_id)
    return [
        Comment(top_level_comment.body, [top_level_comment.score])
        for top_level_comment in submission.comments
    ]


@cache
def get_semantics(_comment: Comment) -> Semantics:
    return Semantics(0, 0)


if __name__ == "__main__":
    main()
