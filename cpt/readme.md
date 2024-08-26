# README

## DELETE MIGRATION BEFORE COMMIT
We don't delete DB data just delete development migrations.

source :https://simpleisbetterthancomplex.com/tutorial/2016/07/26/how-to-reset-migrations.html
```
cd cpt/
find . -path "*/migrations/*.py" 
ind . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete
python manage.py makemigrations
cd ..
python manage.py makemigrations
python manage.py migrate --fake-initial
```
