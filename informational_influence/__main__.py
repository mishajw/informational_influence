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
    parser.add_argument("--subreddit", type=str, default="news")
    parser.add_argument("--num-posts", type=int, default=10)
    parser.add_argument("--fetch-time-sec", type=float, default=10)
    parser.add_argument("--num-fetches", type=int, default=10)

    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_dir():
        output.mkdir()

    num_requests_estimate = 1 + args.num_posts * args.num_fetches
    num_requests_per_minute_estimate = num_requests_estimate / (
        args.fetch_time_sec / 60
    )
    print(f"Estimated num Reddit requests: {num_requests_estimate}")
    print(
        f"Estimated num Reddit requests per minute: "
        f"{num_requests_per_minute_estimate}"
    )

    reddit = create_reddit(args.client_id, args.client_secret)
    posts = get_posts.with_cache(
        output / "posts", reddit, args.subreddit, args.num_posts
    )
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
def get_posts(reddit: Reddit, subreddit: str, num_posts: int) -> List[Post]:
    return [
        Post(post.id)
        for post in reddit.subreddit(subreddit).new(limit=num_posts)
    ]


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
