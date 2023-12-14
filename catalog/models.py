import uuid
from datetime import date

from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


# Create your models here.
class Genre(models.Model):
    """
        Class for book genre model
    """
    name = models.CharField(max_length=200, help_text='Name field for Book Genre')

    def __str__(self):
        """
            Return string Genre name
        """
        return self.name


class Language(models.Model):
    """
        Class for language model
    """

    language_long = models.CharField(max_length=50, help_text='Full Language title of the book')
    language_short = models.CharField(max_length=2, help_text='Short Language title of the book')

    def __str__(self):
        """
            Return string Language name
        """
        return f'{self.language_short}-{self.language_long}'


class Book(models.Model):
    """
        Class for Book model
    """
    title = models.CharField(max_length=200)
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)
    summary = models.TextField(max_length=1000, help_text='Enter brief description for book')
    isbn = models.CharField('ISBN', max_length=13, help_text='13 Character <a href="https://www.isbn-international.org/content/what-isbn">ISBN number</a>')
    genre = models.ManyToManyField(Genre, help_text='Select Genre for this Book')
    cover = models.ImageField(upload_to='books_covers/', null=True, blank=True, default='/books_covers/upscaled_31.jpg')

    def __str__(self):
        """
            Return string name of Book
        """
        return self.title

    def get_absolute_url(self):
        """
            Get link to Book instance
        """
        return reverse('book-detail', args=[str(self.pk)])

    def display_genre(self):
        """
            Func for admin panel Book-Genre display
        """
        return ', '.join([genre.name for genre in self.genre.all()[:3]])
    display_genre.short_description = 'Genre'


class BookInstance(models.Model):
    """
        Model representing a specific copy of a book (i.e. that can be borrowed from the library).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique instance id for search')
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True)
    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True)
    LOAN_STATUS = (
        ('m', 'Maintenance'),
        ('o', 'On loan'),
        ('a', 'Available'),
        ('r', 'Reserved'),
    )

    status = models.CharField(max_length=1, choices=LOAN_STATUS, blank=True, default='m', help_text='Book availability')
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True)

    borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["due_back"]
        permissions = (('can_mark_returned', 'Set book as returned.'), )

    @property
    def is_overdue(self):
        if self.due_back and date.today() > self.due_back:
            return True
        return False

    def __str__(self):
        return f'{self.id} {self.book.title}'


class Author(models.Model):
    """
        Class for Author model
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField('Died', null=True, blank=True)

    class Meta:
        ordering = ['last_name']

    def get_absolute_url(self):
        """
            Get link to Book instance
        """
        return reverse('author-detail', args=[str(self.pk)])

    def __str__(self):
        """
            Return string name of Book
        """
        return f'{self.last_name} {self.first_name}'
