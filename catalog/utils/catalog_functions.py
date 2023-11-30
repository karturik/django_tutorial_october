from ..models import Book


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
