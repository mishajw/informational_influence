# pylint: disable=missing-docstring

from pathlib import Path
from typing import List, NamedTuple
import argparse
import logging
import random
import time

from praw import Reddit
import multiprocess
import numpy as np

from . import cache


LOG = logging.getLogger(__name__)
REDDIT_REQUESTS_PER_SECOND = 1


class Vote(NamedTuple):
    score: int
    time: float


class Comment(NamedTuple):
    text: str
    first_seen: float
    votes: List[Vote]


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
    parser.add_argument("--fetch-time-sec", type=float, default=60)

    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_dir():
        output.mkdir()

    reddit_requests_per_second_per_post = (
        REDDIT_REQUESTS_PER_SECOND / args.num_posts
    )
    fetch_wait_time_sec = 1 / reddit_requests_per_second_per_post
    LOG.info(
        "Waiting for %s seconds between requests per post", fetch_wait_time_sec
    )

    reddit = create_reddit(args.client_id, args.client_secret)
    pool = multiprocess.Pool(args.num_posts)
    posts = get_posts.with_cache(
        output / "posts", reddit, args.subreddit, args.num_posts
    )
    comments = dict(
        pool.map(
            lambda p: (
                p,
                get_comments.with_cache(
                    output / f"comments-{p.post_id}",
                    reddit,
                    p,
                    args.fetch_time_sec,
                    fetch_wait_time_sec,
                ),
            ),
            posts,
        )
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
    LOG.debug("get_posts for r/%s", subreddit)
    return [
        Post(post.id)
        for post in reddit.subreddit(subreddit).new(limit=num_posts)
    ]


@cache
def get_comments(
    reddit: Reddit,
    post: Post,
    fetch_time_sec: float,
    fetch_wait_time_sec: float,
) -> List[Comment]:
    # Sleep for a random amount to stagger the requests
    time.sleep(random.uniform(0, fetch_wait_time_sec))

    LOG.debug("get_comments for %s", post.post_id)
    submission = reddit.submission(post.post_id)

    start_time = time.time()
    fetch_times = np.arange(
        start_time, start_time + fetch_time_sec, fetch_wait_time_sec
    )

    comment_id_dict = dict()
    for i, fetch_time in enumerate(fetch_times):
        # Sleep until fetch_time
        current_time = time.time()
        if current_time < fetch_time:
            time.sleep(fetch_time - current_time)
        LOG.debug(
            "get_comments for %s at time %f (%d/%d)",
            post.post_id,
            fetch_time,
            i + 1,
            len(fetch_times),
        )
        # Get post's comments
        for top_level_comment in submission.comments:
            comment_id = top_level_comment.id
            if comment_id not in comment_id_dict:
                comment_id_dict[comment_id] = Comment(
                    top_level_comment.body, current_time, []
                )
            comment_id_dict[comment_id].votes.append(
                Vote(top_level_comment.score, current_time)
            )

    LOG.debug(
        "get_comments for %s finished with %d comments",
        post.post_id,
        len(comment_id_dict),
    )

    return list(comment_id_dict.values())


@cache
def get_semantics(_comment: Comment) -> Semantics:
    return Semantics(0, 0)


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("prawcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    main()
