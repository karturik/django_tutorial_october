from django.contrib import admin
from .models import Book, Genre, Language, Author, BookInstance


# Register your models here.
@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_display = ('book', 'due_back', 'language', 'status', 'borrower')
    list_filter = ('status', 'language', 'due_back')

    fieldsets = (
        ('Instance Data', {
            'fields': ('book', 'imprint', 'id')
                }),
        ('Availability', {
            'fields': ('status', 'due_back', 'borrower')
        }),
    )


class BookInstanceInline(admin.TabularInline):
    model = BookInstance
    extra = 0


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'display_genre', 'isbn')
    inlines = [BookInstanceInline]


class BookInline(admin.TabularInline):
    exclude = ['summary']
    model = Book
    extra = 0


class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'date_of_birth', 'date_of_death')
    fields = ['last_name', 'first_name', ('date_of_birth', 'date_of_death')]
    inlines = [BookInline]


admin.site.register(Author, AuthorAdmin)
# admin.site.register(Book, BookAdmin)
# admin.site.register(BookInstance, BookInstanceAdmin)
admin.site.register(Genre)
admin.site.register(Language)

