# pylint: disable=missing-docstring

from pathlib import Path
from typing import List, NamedTuple
import argparse

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
    parser.add_argument("--output", type=str, default="output")
    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_dir():
        output.mkdir()

    posts = get_posts()
    comments = dict((p, get_comments(p)) for p in posts)
    semantics = dict(
        (p, [get_semantics(c) for c in comments[p]]) for p in posts
    )

    print("comments", comments)
    print("semantics", semantics)


@cache
def get_posts() -> List[Post]:
    return []


@cache
def get_comments(_post: Post) -> List[Comment]:
    return []

@cache
def get_semantics(_comment: Comment) -> Semantics:
    return Semantics(0, 0)


if __name__ == "__main__":
    main()
