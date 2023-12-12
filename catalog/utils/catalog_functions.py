import os
import json
import requests

from locallibrary.settings import MEDIA_ROOT
from ..models import Book, Author, Genre


def get_max_viewed_book(user_session: dict) -> Book | None:
    """
        Получаем наиболее просматриваемую пользователем книгу
    """
    books_views_keys = [key for key in user_session.keys() if 'book' in key and 'views' in key]
    if books_views_keys:
        max_viewed_book = max(books_views_keys, key=lambda key: user_session[key])
        max_viewed_book_id = int(max_viewed_book.replace('book_', '').replace('_views', ''))

        max_viewed_book = Book.objects.get(pk=max_viewed_book_id)
    else:
        max_viewed_book = None

    return max_viewed_book


def download_book_covers(url: str) -> str:
    headers = {
        "authority": "litnet.com",
        "method": "GET",
        "path": "/ru/genres",
        "scheme": "https",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru,en;q=0.9,pl;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://litnet.com/ru",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.731"
    }

    image_name = url.split('/')[-1]
    image_path = os.path.join(MEDIA_ROOT, 'books_covers', image_name)
    if not os.path.exists(image_path):
        r = requests.get(url, headers=headers, stream=True)
        with open(image_path, 'wb') as file:
            file.write(r.content)

    return image_name


def get_new_books_to_db() -> tuple[int, int]:
    saved_books = 0
    books_datas = 0

    for json_file in os.listdir('data_files'):
        if 'books_data' in json_file and '.json' in json_file:
            with open(os.path.join('data_files', json_file), 'r', encoding='utf-8') as src_file:
                books_datas = json.load(src_file)

            if books_datas:
                for book_data in books_datas:
                    try:
                        book_title = book_data['book_title']
                        author = book_data['author'].split(' ', 1)
                        summary = book_data['summary']
                        category = book_data['category']
                        image_link = book_data['image_link']

                        new_author, created = Author.objects.get_or_create(first_name=author[0], last_name=author[1])

                        new_genre, created = Genre.objects.get_or_create(name=category)

                        genres_for_book = Genre.objects.filter(name=category)

                        image_name = download_book_covers(image_link)

                        new_book, created = Book.objects.get_or_create(title=book_title, author=new_author,
                                        summary=summary, genre=genres_for_book,
                                        cover=os.path.join('books_covers', image_name))

                        saved_books += 1

                    except Exception as e:
                        print(e)

    return saved_books, len(books_datas)
