import requests
from bs4 import BeautifulSoup
import sqlite3
import time

url = "https://kino.mail.ru/cinema/all/?page="

mail = "https://kino.mail.ru/"

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

#Находим количество страниц с фильмами
pagenums = soup.find_all("a", class_="p-pager__list__item")
max_page = int(pagenums[-1].text)+1

conn = sqlite3.connect('films.db')

#Коннектимся сразу, т.к. мы знаем, что наш код работает без ошибок
cur = conn.cursor()

#Создаем таблицу, если её нет
cur.execute("""CREATE TABLE IF NOT EXISTS films(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    score REAL,
    year INT,
    genre TEXT,
    description TEXT,
    image TEXT,
    country TEXT);
    """)

#Список стран, который понадобиться позже
country_list = ['США', 'Россия', 'СССР', 'Франция', 'Великобритания', 'Беларусь', 'Германия', 'Гонконг', 'Индия', 'Испания', 'Италия', 'Казахстан', 'Канада', 'Украина', 'Япония', 'Бельгия', 'Австралия', 'Китай', 'Польша', 'Швеция', 'Дания', 'Южная Корея', 'Нидерланды', 'Швейцария', 'Мексика', 'Чешская Республика', 'Ирландия', 'Аргентина', 'Бразилия', 'Венгрия', 'Австрия', 'Финляндия', 'Норвегия', 'Румыния', 'Израиль', 'Португалия', 'Южная Африка', 'Болгария', 'Таиланд', 'Новая Зеландия', 'Турция', 'Греция', 'Иран', 'Югославия', 'Исландия', 'Люксембург', 'Словакия', 'Чили', 'Латвия', 'Сербия', 'Тайвань (Китай)', 'Колумбия', 'Эстония', 'Филиппины', 'Сингапур', 'Литва', 'Хорватия', 'Грузия', 'Индонезия', 'Куба', 'Армения', 'Словения', 'Катар', 'ОАЭ', 'Египет', 'Уругвай', 'Марокко', 'Ливан', 'Малайзия', 'Вьетнам', 'Алжир', 'Босния и Герцеговина', 'Перу', 'Тунис', 'Республика Македония', 'Узбекистан', 'Венесуэла', 'Кипр', 'Азербайджан', 'Киргизия', 'Монголия', 'Пуэрто-Рико', 'Кения', 'Пакистан', 'Ирак', 'Нигерия', 'Сирийская Арабская Республика', 'Шри-Ланка', 'Албания', 'Черногория', 'Саудовская Аравия', 'Афганистан', 'Палестинская территория', 'Сенегал', 'Мальта', 'Боливия', 'Коста-Рика', 'Камбоджа']

#Итерация по страницам
for i in range(1, max_page):
    startTime = time.time()

    # Отправить GET-запрос на страницу
    response = requests.get(url+str(i))  
    soup = BeautifulSoup(response.text, "html.parser")

    #Получения ссылок на каждый фильм со страницы
    films = soup.find_all("a", class_="link link_inline link-holder link-holder_itemevent link-holder_itemevent_small")
    
    #Итерация по ссылкам
    for index, film in enumerate(films, start=1):
        response = requests.get(mail+film.get("href"))

        soup = BeautifulSoup(response.text, "html.parser")
        #Заполняем наши данные
        film_title = soup.find("h1", class_="text text_bold_giant color_white")
        parent_score = soup.find("span", class_="text text_bold_medium text_fixed")

        #Проверяем, чтобы была оценка. Фильмы без оценки выдадут ошибку. Если они нужны, можно создать исключение
        if parent_score:
            film_score = parent_score.find("span", class_="margin_left_10")
        film_year = soup.find("a", class_="color_black")
        film_genre = soup.find_all("span", class_="badge__text")
        film_description = soup.find("span", "p", class_="text text_inline text_light_medium text_fixed valign_baseline")
        film_image = soup.find("img", class_="picture__image picture__image_cover")
        film_countries = soup.find_all("span", "a", class_="p-truncate__inner js-toggle__truncate-inner")
        
        #Ищем страны производства фильма, т.к. с этим тегом и классом идут актеры и другая информация
        film_country = ""
        for country in film_countries:
            for count in country_list:
                if count in country.text:
                    film_country=country.text
                    break

        #Проверяем, чтобы у фильма был постер и тогда добавляем его в бд
        if film_image.get("src") != '/img/v2/nopicture/308x462@2x.png':
            if film_country and film_description and film_genre and film_score:
                title = film_title.text
                score = float(film_score.text)
                year = int(film_year.text)
                genre = ', '.join([genre.text for genre in film_genre])
                description = film_description.text
                image = film_image.get("src")
                country = film_country

                film = (title, score, year, genre, description, image, country)

                cur.execute("INSERT INTO films VALUES (NULL, ?, ?, ?, ?, ?, ?, ?);", film)

    endTime = time.time()
    #Следим за выполнением парсера
    print(f'Страница {i} выполнена за {endTime-startTime} секунд')

#Закрываем подключение в конце, потому что код работает
conn.commit()
