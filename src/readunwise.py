import argparse
import logging
import random
from discord import Client, Embed
from highlight import Highlight

CLIPPING_DELIMITER = "=========="
MAX_FIELD_SIZE = 1024


class ReadUnwiseClient(Client):
    def __init__(self):
        super().__init__()
        self._channel = None
        self._highlights_by_book = _load_highlights()

    def send(self):
        self.run(args.discord_token)

    async def on_ready(self):
        self._channel = self.get_channel(args.discord_channel)

        logging.info("Sending message...")
        await self._send_message()

        logging.info("Exiting...")
        await self.close()

    async def _send_message(self):
        random_book = self._get_random_book()
        selected_highlights = self._select_highlights(random_book)
        embed = _create_embed(random_book, selected_highlights)
        await self._channel.send(embed=embed)

    def _get_random_book(self) -> str:
        books = list(self._highlights_by_book.keys())
        return random.choice(books)

    def _select_highlights(self, book: str) -> list:
        book_highlights = self._highlights_by_book[book]
        n_highlights = min(len(book_highlights), args.n_highlights)
        return random.sample(book_highlights, k=n_highlights)


def _load_highlights() -> dict:
    highlights = {}
    loaded = 0

    with open(args.clippings_file, "r+", encoding="utf8") as f:
        clippings = f.read().split(CLIPPING_DELIMITER)

    for clipping in clippings:
        highlight = Highlight.create(clipping)
        if highlight is not None:
            highlights.setdefault(highlight.book, []).append(highlight)
            loaded += 1

    logging.info(f"Found {loaded} highlights across {len(highlights)} books")
    return highlights


def _create_embed(book: str, highlights: list) -> Embed:
    embed = Embed(title=f"**📘 {book}**", color=0xfffff)
    [embed.add_field(name="━" * 10, value=_format_content(highlight.content), inline=False) for highlight in highlights]
    return embed


def _format_content(content: str) -> str:
    field = f"⭐ {content}"
    return field[:MAX_FIELD_SIZE]


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p", level=logging.INFO)
    logging.getLogger("discord").setLevel(logging.ERROR)

    parser = argparse.ArgumentParser(description="Send randomly selected Kindle highlights to a Discord channel.")
    parser.add_argument("clippings_file", help="clippings text file from Kindle device (/documents/My Clippings.txt)")
    parser.add_argument("discord_token", help="discord bot authentication token")
    parser.add_argument("discord_channel", type=int,  help="discord channel ID")
    parser.add_argument("--n", type=int, default=3, dest="n_highlights", help="number of highlights to include in message (default: %(default)s)")

    args = parser.parse_args()
    logging.info(f"Config: {vars(args)}")

    ReadUnwiseClient().send()
