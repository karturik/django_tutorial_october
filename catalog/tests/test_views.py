import datetime

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission # Необходимо для представления User как borrower
from django.utils import timezone

from catalog.models import BookInstance, Book, Genre, Language, Author


class BookListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create 13 books for pagination tests
        number_of_books = 13
        for book_num in range(number_of_books):
            Book.objects.create(title='Book Number %s.' % book_num)

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get('/catalog/books/')
        self.assertEqual(resp.status_code, 200)

    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('books'))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        resp = self.client.get(reverse('books'))
        self.assertEqual(resp.status_code, 200)

        self.assertTemplateUsed(resp, 'catalog/books_list_page.html')

    def test_pagination_is_ten(self):
        resp = self.client.get(reverse('books'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] == True)
        self.assertTrue(len(resp.context['book_list']) == 10)

    def test_lists_all_books(self):
        # Get second page and confirm it has (exactly) remaining 3 items
        resp = self.client.get(reverse('books')+'?page=2')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] == True)
        self.assertTrue(len(resp.context['book_list']) == 3)


class LoanedBookInstancesByUserListViewTest(TestCase):

    def setUp(self):
        # Создание двух пользователей
        test_user1 = User.objects.create_user(username='testuser1', password='12345')
        test_user1.save()
        test_user2 = User.objects.create_user(username='testuser2', password='12345')
        test_user2.save()

        # Создание книги
        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(language_long='English')
        test_book = Book.objects.create(title='Book Title', summary = 'My book summary',
                                        isbn='ABCDEFG', author=test_author)
        # Create genre as a post-step
        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book) # Присвоение типов many-to-many напрямую недопустимо
        test_book.save()

        # Создание 30 объектов BookInstance
        number_of_book_copies = 30
        for book_copy in range(number_of_book_copies):
            return_date = timezone.now() + datetime.timedelta(days=book_copy%5)
            if book_copy % 2:
                the_borrower = test_user1
            else:
                the_borrower = test_user2
            status = 'm'
            BookInstance.objects.create(book=test_book, imprint='Unlikely Imprint, 2016',
                                        due_back=return_date, borrower=the_borrower,
                                        status=status)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(resp, '/users/login/?next=/catalog/mybooks/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Проверка, что пользователь залогинился
        self.assertEqual(str(resp.context['user']), 'testuser1')
        # Проверка ответа на запрос
        self.assertEqual(resp.status_code, 200)

        # Проверка того, что мы используем правильный шаблон
        self.assertTemplateUsed(resp, 'catalog/bookinstance_list_borrowed_user.html')

    def test_only_borrowed_books_in_list(self):
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Проверка, что пользователь залогинился
        self.assertEqual(str(resp.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(resp.status_code, 200)

        # Проверка, что изначально у нас нет книг в списке
        self.assertTrue('bookinstance_list' in resp.context)
        self.assertEqual(len(resp.context['bookinstance_list']), 0)

        # Теперь все книги "взяты на прокат"
        get_ten_books = BookInstance.objects.all()[:10]

        for copy in get_ten_books:
            copy.status = 'o'
            copy.save()

        # Проверка, что все забронированные книги в списке
        resp = self.client.get(reverse('my-borrowed'))
        # Проверка, что пользователь залогинился
        self.assertEqual(str(resp.context['user']), 'testuser1')
        # Проверка успешности ответа
        self.assertEqual(resp.status_code, 200)

        self.assertTrue('bookinstance_list' in resp.context)

        # Подтверждение, что все книги принадлежат testuser1 и взяты "на прокат"
        for bookitem in resp.context['bookinstance_list']:
            self.assertEqual(resp.context['user'], bookitem.borrower)
            self.assertEqual('o', bookitem.status)

    def test_pages_ordered_by_due_date(self):

        # Изменение статуса на "в прокате"
        for copy in BookInstance.objects.all():
            copy.status = 'o'
            copy.save()

        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Пользователь залогинился
        self.assertEqual(str(resp.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(resp.status_code, 200)

        # Подтверждение, что из всего списка показывается только 10 экземпляров
        self.assertEqual(len(resp.context['bookinstance_list']), 10)

        last_date = 0
        for copy in resp.context['bookinstance_list']:
            if last_date == 0:
                last_date = copy.due_back
            else:
                self.assertTrue(last_date <= copy.due_back)


class RenewBookInstancesViewTest(TestCase):

    def setUp(self):
        # Создание пользователя
        test_user1 = User.objects.create_user(username='testuser1', password='12345')
        test_user1.save()

        test_user2 = User.objects.create_user(username='testuser2', password='12345')
        test_user2.save()

        permission = Permission.objects.get(name='Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        # Создание книги
        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(language_ling='English')
        test_book = Book.objects.create(title='Book Title', summary = 'My book summary',
                                        isbn='ABCDEFG', author=test_author,
                                        language=test_language,)

        # Создание жанра Create genre as a post-step
        genre_objects_for_book = Genre.objects.all()
        test_book.genre = genre_objects_for_book
        test_book.save()

        # Создание объекта BookInstance для пользователя test_user1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance1 = BookInstance.objects.create(book=test_book, imprint='Unlikely Imprint, 2016',
                                                              due_back=return_date, borrower=test_user1, status='o')

        # Создание объекта BookInstance для пользователя test_user2
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance2 = BookInstance.objects.create(book=test_book, imprint='Unlikely Imprint, 2016',
                                                            due_back=return_date, borrower=test_user2, status='o')

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))
        # Manually check redirect (Can't use assertRedirect, because the redirect URL is unpredictable)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/users/login/'))

    def test_redirect_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))

        # Manually check redirect (Can't use assertRedirect, because the redirect URL is unpredictable)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/user/login/'))

    def test_logged_in_with_permission_borrowed_book(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance2.pk, }))

        # Check that it lets us login - this is our book and we have the right permissions.
        self.assertEqual(resp.status_code, 200)

    def test_logged_in_with_permission_another_users_borrowed_book(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))

        # Check that it lets us login. We're a librarian, so we can view any users book
        self.assertEqual(resp.status_code, 200)

    def test_HTTP404_for_invalid_book_if_logged_in(self):
        import uuid
        test_uid = uuid.uuid4()  # unlikely UID to match our bookinstance!
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': test_uid, }))
        self.assertEqual(resp.status_code, 404)

    def test_uses_correct_template(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))
        self.assertEqual(resp.status_code, 200)

        # Check we used correct template
        self.assertTemplateUsed(resp, 'catalog/book_renew_librarian.html')