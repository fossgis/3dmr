docker-compose up --build -d
docker-compose exec web python manage.py collectstatic --noinput
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose restart web
