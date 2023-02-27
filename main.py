import os
import sqlite3 as sql
import shutil as shut


global bookDB

def database_validation():
    global bookDB
    if not os.path.exists("books.db"):
        print("Не был найден файл книжной библиотеки.\n1. Создать библиотеку\n2. Импортировать существующую")
        choice = int(input())
        if choice == 1:
            bookDB = sql.connect("books.db")
        elif choice == 2:
            on_loop = True
            while on_loop:
                print("Введите полную директорию до файла базы данных (books.db): ")
                DBpath = input()
                if os.path.exists(DBpath) and os.path.basename(DBpath).endswith(".db"):
                    shut.copy(DBpath, os.getcwd())
                    bookDB = sql.connect(os.path.basename(DBpath))
                    print("База данных успешно импортирована!")
                    break
                else:
                    print("Файл базы данных не найден, попробовать ещё раз? [Y/N]")
                    choice = input().lower()
                    if choice != "y":
                        print("Выходим из программы...")
                        exit()
        else:
            print("Неверный ввод")
            input()
            exit()
    else:
        bookDB = sql.connect("books.db")
    cur = bookDB.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS books(
        book_id INT PRIMARY_KEY,
        book_name TEXT NOT NULL,
        genre TEXT,
        total_pages INT,
        current_pages INT DEFAULT 0,
        note TXT,
        complete INT
    );""")

def DBSearch():
    cur = bookDB.cursor()
    print("Что будем просматривать?\n1. Вся библиотека\n2. Своя выборка")
    choice = int(input())
    if choice == 1:
        cur.execute("""SELECT * FROM books""")
        library = cur.fetchall()
        if library != [] and library[0] != None:
            for books in library:
                print(f"----------\nID: {books[0]}  Название: {books[1]}, Жанр: {books[2]}, Суммарно страниц: {books[3]}, Страниц прочитано: {books[4]}, Прочитана: {(books[6] == 1)}, Заметки: {books[5] if books[5] != '' else None}\n----------")
        else:
            print("Ничего не найдено")
    if choice == 2:
        print("Краткая справка\nВ таблице books по умолчанию существуют атрибуты: book_id, book_name, genre, total_pages, current_pages, note, complete\nЧто-бы например получить только имена всех книг в библиотеке, нужно ввести запрос 'SELECT book_name FROM books'\nЧто-бы получить конкретную выборку, например если требуются книги жанра детектив то следует ввести 'SELECT book_name FROM books WHERE genre = 'Детектив''")
        sql_query = input("Введите SQL запрос: ")
        try:
            cur.execute(sql_query)
            library = cur.fetchall()
            if library != []:
                for books in library:
                    for attribute in books:
                        print(f'| {attribute} ', end="|")
                    print()
            else:
                print("Ничего не найдено")
            input()
        except sql.Error as error:
            print("Ошибка выполнения SQL запроса:", error)


def DBUpdate():
    cur = bookDB.cursor()
    print("1. Добавить книгу в библиотеку\n2. Изменить данные о книге\n3. Удалить книгу из библиотеки")
    choice = int(input())
    if choice == 1:
        cur.execute("""SELECT MAX(book_id) from books""")
        result = cur.fetchone()
        if result[0] == None:
            book_id = 1
        else:
            book_id = result[0] + 1
        try:
            book_name = input("*Введите название книги: ")
            if book_name == "":
                print("Обязательное поле: Название не может быть пустым!")
                input()
                return None
            book_genre = input("Введите жанр или тематику книги: ")
            book_total_pages = int(input("Введите суммарное количество страниц в книге: "))
            if book_total_pages < 0:
                print("Суммарное количество страниц в книге не может быть отрицательным.")
                return None
            book_current_page = int(input("Введите страницу, на которой вы закончили чтение (если не начали - 0): "))
            if not (0 <= book_current_page <= book_total_pages):
                print("Введена некорректная текущая страница, она не может принимать отрицательное значение или быть больше суммарного количества страниц в книге.")
                input()
                return None
            book_note = input("Если треубется, введите заметку: ")
            book_completed = input("Вы завершили чтение книги? [Y/N]")
            if book_completed.lower() == 'y':
                book_completed = 1
            elif book_completed.lower() == 'n':
                book_completed = 0
            else:
                raise TypeError
            book_info = (book_id, book_name, book_genre, book_total_pages, book_current_page, book_note, book_completed)
            cur.execute("""INSERT INTO books (book_id,book_name,genre,total_pages,current_pages,note,complete) VALUES (?,?,?,?,?,?,?)""", book_info)
            bookDB.commit()
            print("Книга успешно занесена в библиотеку!")
        except TypeError:
            print("Введены некорректные данные о книге")
        except sql.Error as error:
            print("Ошибка записи в базу данных!\n", error)
    elif choice == 2:
        #Если будут дубликаты?
        book_name = input("Введите название книги: ")
        cur.execute("""SELECT COUNT(book_name) FROM books WHERE book_name LIKE ?""", (book_name,))
        result = cur.fetchone()[0]
        if result == 1:
            print("Что вы хотите изменить?\n1. Название книги\n2. Жанр\n3. Количество страниц в книге\n4. Текущую страницу\n5. Заметку\n6. Отметить книгу как прочитанную/не прочитанную")
            choice = int(input())
            if choice == 1:
                new_name = input("Введите новое название книги: ").strip()
                cur.execute("UPDATE books SET book_name = ? WHERE book_name LIKE ?", (new_name, book_name,))
                bookDB.commit()
                print("Статус книги успешно изменён")
            elif choice == 2:
                new_genre = input("Введите новый жанр: ").strip()
                cur.execute("UPDATE books SET genre = ? WHERE book_name LIKE ?", (new_genre, book_name,))
                bookDB.commit()
                print("Статус книги успешно изменён")
            elif choice == 3:
                new_total = input("Введите новое количество страниц в книге: ")
                if int(new_total) < 0:
                    print("Суммарное количество страниц в книге не может быть отрицательным")
                    return None
                cur.execute("UPDATE books SET total_pages = ? WHERE book_name LIKE ?", (new_total, book_name,))
                bookDB.commit()
                print("Статус книги успешно изменён")
            elif choice == 4:
                new_curpage = input("Введите страницу на которой вы остановили чтение: ")
                cur.execute("""SELECT total_pages FROM books WHERE book_name LIKE ?""", (book_name,))
                actual_total_pages = cur.fetchone()[0]
                print(actual_total_pages)
                if not (0 <= int(new_curpage) <= actual_total_pages):
                    print("Введена некорректная текущая страница, она не может принимать отрицательное значение или быть больше суммарного количества страниц в книге.")
                    input()
                    return None
                cur.execute("UPDATE books SET current_pages = ? WHERE book_name LIKE ?", (new_curpage, book_name,))
                bookDB.commit()
                print("Статус книги успешно изменён")
            elif choice == 5:
                new_note = input("Введите новую заметку")
                cur.execute("UPDATE books SET note = ? WHERE book_name LIKE ?", (new_note, book_name,))
                bookDB.commit()
                print("Статус книги успешно изменён")
            elif choice == 6:
                cur.execute("""SELECT complete FROM books WHERE book_name LIKE ?""", (book_name,))
                result = cur.fetchone()[0]
                if result == 0:
                    cur.execute("UPDATE books SET complete = ? WHERE book_name LIKE ?", (1, book_name,))
                else:
                    cur.execute("UPDATE books SET complete = ? WHERE book_name LIKE ?", (0, book_name,))
                print("Статус книги успешно изменён")
                bookDB.commit()
        elif result == 0:
            print("Книги с таким названием не обнаружено")
        else:
            #Сценарий если будут найдены дубликаты
            pass
    elif choice == 3:
        book_name = input("Введите название книги: ")
        cur.execute("""SELECT COUNT(book_name) FROM books WHERE book_name LIKE ?""", (book_name,))
        result = cur.fetchone()[0]
        if result == 1:
            cur.execute("""DELETE FROM books WHERE book_name = ?""", (book_name,))
            bookDB.commit()
            print(f"Книга {book_name} успешно удалена из библиотеки")
        elif result == 0:
            print("Книги с таким названием не обнаружено")
        else:
            #Сценарий если будут найдены дубликаты
            pass
    else:
        print("Неверный ввод")
    input()

def DBExport():
    choice = int(input("Экспорт/Удаление. \n1. Удалить базу данных\n2. Экспортировать базу данных.\n"))
    if choice == 1:
        print("Вы точно хотите удалить базу данных? [Y/N]")
        choice = input()
        if choice.lower() == 'y':
            bookDB.close()
            os.remove("books.db")
            print("База данных успешно удалена!")
            input()
            exit()
    elif choice == 2:
        export_path = input("Введите директорию для экспорта файла: ")
        if os.path.exists(export_path):
            try:
                shut.copy(os.path.abspath('books.db'), export_path)
                print("База данных успешно экспортирована.")
            except:
                print("Произошла ошибка экспорта!")

def Main():
    global bookDB
    main_loop = True
    first_iteration = True
    while main_loop:
        if first_iteration:
            print('Добро пожаловать в "Library".\nЭта утилита создана для того, чтобы отслеживать прогресс чтения различных книг или документации, а так-же хранения заметок об этих книгах. \nФактический программа является оболочкой для работы с базой данных. Навигация осуществляется выбором номеров функций программы.')
            first_iteration = False
        print("И так, что будем делать?\n1. Просмотр библиотеки\n2. Обновление данных в библиотеке\n3. Экспорт/удаление базы данных.\n4. Выход из программы")
        choice = int(input())
        if choice == 1:
            DBSearch()
        elif choice == 2:
            DBUpdate()
        elif choice == 3:
            DBExport()
        elif choice == 4:
            exit()
        else:
            print("Неверный ввод")
            input()



if __name__ == '__main__':
    database_validation()
    Main()
