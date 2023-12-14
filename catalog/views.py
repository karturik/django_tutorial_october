import datetime
import io

import pandas as pd

from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.forms import model_to_dict
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, FileResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from .utils import get_max_viewed_book, get_new_books_to_db
from .models import Author, Book, BookInstance, Genre
from .forms import RenewBookForm, UploadBookForm


def index(request):
    """
        Function for main index page representation
    """
    # Count of books and booksinstances
    num_book = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Count of all available instances
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # Authors count
    num_authors = Author.objects.count()

    # Visits count
    num_visits = request.session.get('home_page_num_visits', 0)
    request.session['home_page_num_visits'] = num_visits + 1

    if request.user.is_authenticated:
        max_viewed_book = get_max_viewed_book(request.session)
    else:
        max_viewed_book = None

        # print(max_viewed_book)
    context = {
        'num_book': num_book,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
        'max_viewed_book': max_viewed_book
    }

    return render(request, 'index.html', context=context)


class BookListView(generic.ListView):
    model = Book
    template_name = 'catalog/books_list_page.html'
    paginate_by = 10


class BookDetailView(LoginRequiredMixin, generic.DetailView):
    model = Book
    template_name = 'catalog/book_detail_page.html'

    def get(self, request, *args, **kwargs):
        book_id = kwargs['pk']
        book_key = f'book_{book_id}_views'
        if book_key not in request.session:
            request.session[book_key] = 1
        else:
            request.session[book_key] += 1
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book_id = self.kwargs['pk']
        book_key = f'book_{book_id}_views'
        context['book_views'] = self.request.session.get(book_key, 0)
        return context


@login_required
def authors_list_view(request):
    authors = Author.objects.all()

    paginator = Paginator(authors, 3)
    # 3 posts in each page
    page = request.GET.get('page')
    try:
        authors_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        authors_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range deliver last page of results
        authors_list = paginator.page(paginator.num_pages)

    context = {
        # 'authors_list': authors_list,
        'page_obj': authors_list,
        'is_paginated': True
    }

    return render(request, 'catalog/authors_list_page.html', context=context)


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
        Generic class-based view listing books on loan to current user.
    """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class AllLoanedBooksListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    """
        Generic class-based view listing all loaned books for librarian
    """
    permission_required = 'catalog.can_mark_returned'

    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    book_inst = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        # Создаём экземпляр формы и заполняем данными из запроса (связывание, binding):
        form = RenewBookForm(request.POST)

        # Проверка валидности данных формы:
        if form.is_valid():
            # Обработка данных из form.cleaned_data
            # (здесь мы просто присваиваем их полю due_back)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()
            messages.success(request, "Book's date updated successfully!")
            # Переход по адресу 'all-borrowed':
            return HttpResponseRedirect(reverse('all-borrowed'))

    else:
        messages.warning(request, "Update book's date carefully!")
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date, })

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst': book_inst})


class AuthorCreate(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    permission_required = 'catalog.can_mark_returned'

    model = Author
    fields = '__all__'
    # initial = {'date_of_death': '12/10/2023',}

    success_url = reverse_lazy('authors')


class AuthorUpdate(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    permission_required = 'catalog.can_mark_returned'

    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']

    success_url = reverse_lazy('authors')


class AuthorDelete(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = 'catalog.can_mark_returned'

    model = Author
    success_url = reverse_lazy('authors')


class BookCreate(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.CreateView):
    permission_required = 'catalog.can_mark_returned'

    model = Book
    fields = '__all__'
    success_url = reverse_lazy('books')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Book created success.")
        return response


class BookUpdate(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    permission_required = 'catalog.can_mark_returned'

    model = Book
    fields = '__all__'

    success_url = reverse_lazy('books')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Book update success!")
        return response


class BookDelete(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = 'catalog.can_mark_returned'

    model = Book
    success_url = reverse_lazy('books')


# @permission_required('catalog.can_mark_returned')
# def parse_files_with_books(request):
#     saved_books_count, founded_books_count = get_new_books_to_db()
#
#     context = {
#         'saved_books_count': saved_books_count,
#         'founded_books_count': founded_books_count
#     }
#
#     return render(request, 'staf_pages/new_books.html', context=context)


@permission_required('catalog.can_mark_returned')
def parse_files_with_books(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        file_data = file.read()
        file_format = file.name.split('.')[-1]
        saved_books_count, founded_books_count = get_new_books_to_db(file_data)
        return render(request, 'staf_pages/books_upload_finish.html', context={'saved_books_count': saved_books_count,
                                                                               'founded_books_count': founded_books_count})
    else:
        form = UploadBookForm
        return render(request, 'staf_pages/new_books.html', context={'form': form})


def export_all_books(request):
    if request.method == 'POST':
        queryset = Book.objects.all()
        data = [model_to_dict(book) for book in queryset]
        # Convert the data to a pandas DataFrame
        df = pd.DataFrame(data)

        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        # Create FileResponse object
        filename = f'all_books_{datetime.datetime.now()}.xlsx'
        response = FileResponse(buffer, as_attachment=True, filename=filename)

        return response
