****
![foodgram-project-react Workflow Status](https://github.com/xofmdo/foodgram-project-react/actions/workflows/main.yml/badge.svg)
# Продуктовый помощник Foodgram 


[![Python](https://img.shields.io/badge/-Python-464646?style=flat&logo=Python&logoColor=56C0C0&color=008080)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat&logo=Django&logoColor=56C0C0&color=008080)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat&logo=Django%20REST%20Framework&logoColor=56C0C0&color=008080)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat&logo=PostgreSQL&logoColor=56C0C0&color=008080)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat&logo=NGINX&logoColor=56C0C0&color=008080)](https://nginx.org/ru/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat&logo=gunicorn&logoColor=56C0C0&color=008080)](https://gunicorn.org/)
[![Docker](https://img.shields.io/badge/-Docker-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/)
[![Docker-compose](https://img.shields.io/badge/-Docker%20compose-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/)
[![Docker Hub](https://img.shields.io/badge/-Docker%20Hub-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/products/docker-hub)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat&logo=GitHub%20actions&logoColor=56C0C0&color=008080)](https://github.com/features/actions)
[![Yandex.Cloud](https://img.shields.io/badge/-Yandex.Cloud-464646?style=flat&logo=Yandex.Cloud&logoColor=56C0C0&color=008080)](https://cloud.yandex.ru/)

## Описание проекта Foodgram
«Продуктовый помощник»: приложение, на котором пользователи публикуют рецепты, 
подписываться на публикации других авторов и добавлять рецепты в избранное. 
Сервис «Список покупок» позволит пользователю создавать список продуктов, 
которые нужно купить для приготовления выбранных блюд. 

## Запуск проекта в dev-режиме

- Клонируйте репозиторий с проектом на свой компьютер. В терминале из рабочей директории выполните команду:
```bash
git clone https://github.com/Mrazzzlop/foodgram-project-react.git
```

- Установить и активировать виртуальное окружение

```bash
source /venv/bin/activate
```

- Установить зависимости из файла requirements.txt

```bash
python -m pip install --upgrade pip
```
```bash
pip install -r requirements.txt
```
- Создать файл .env в папке проекта:
```.env
DB_ENGINE=django.db.backends.postgresql # указываем, что работаем с postgresql
DB_NAME=postgres # имя базы данных
POSTGRES_USER=postgres # логин для подключения к базе данных
POSTGRES_PASSWORD=postgres # пароль для подключения к БД (установите свой)
DB_HOST=db # название сервиса (контейнера)
DB_PORT=5432 # порт для подключения к БД
DEBUG=0
```

### Выполните миграции:
```bash
python manage.py migrate
```

- В папке с файлом manage.py выполнить команду:
```bash
python manage.py runserver
```

- Создание нового супер пользователя 
```bash
python manage.py createsuperuser
```

### Загрузите статику:
```bash
python manage.py collectstatic --no-input
```
### Заполните базу тестовыми данными: 
```bash
python manage.py add_tags_from_data
python manage.py add_ingidients_from_data 
```


## Запуск проекта через Docker

Установите Docker, используя инструкции с официального сайта:
- для [Windows и MacOS](https://www.docker.com/products/docker-desktop)
- для [Linux](https://docs.docker.com/engine/install/ubuntu/). Отдельно потребуется установть [Docker Compose](https://docs.docker.com/compose/install/)

Клонируйте репозиторий с проектом на свой компьютер.
В терминале из рабочей директории выполните команду:
```bash
git clone https://github.com/Mrazzzlop/foodgram-project-react.git
```

- в Docker cоздаем образ :
```bash
docker build -t foodgram .
```

Выполните команду:
```bash
cd ../infra
docker-compose up -d --build
```

- В результате должны быть собрано три контейнера, при введении следующей команды получаем список запущенных контейнеров:  
```bash
docker-compose ps
```
Назначение контейнеров:  

|             IMAGES             | NAMES                |        DESCRIPTIONS         |
|:------------------------------:|:---------------------|:---------------------------:|
|          nginx:1.19.3          | infra-_nginx_1       |   контейнер HTTP-сервера    |
|         postgres:12.4          | infra-_db_1          |    контейнер базы данных    |
| mrazzzlop/foodgram_back:latest | infra-_backend_1     | контейнер приложения Django |
| mrazzzlop/foodgram_ront:latest | infra-_frontend_1    | контейнер приложения React  |


### Выполните миграции:
```bash
docker-compose exec backend python manage.py migrate
```
### Создайте суперпользователя:
```bash
docker-compose exec backend python manage.py createsuperuser
```

### Загрузите статику:
```bash
docker-compose exec backend python manage.py collectstatic --no-input
```

### Заполните базу тестовыми данными:
```bash
docker-compose exec backend python manage.py add_tags_from_data
docker-compose exec backend python manage.py add_ingidients_from_data   
```


### Основные адреса: 

| Адрес                 | Описание |
|:----------------------|:---------|
| 127.0.0.1            | Главная страница |
| 127.0.0.1/admin/     | Для входа в панель администратора |
| 127.0.0.1/api/docs/  | Описание работы API |

### Автор:  
_Вторушин Александр_<br>
**email**: _mrazzzlop@gmail.com_<br>
**telegram** _@mrazzzlop_ 