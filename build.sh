set -o errexit

echo "starting build"

rm -rf "staticfiles"


pip install -r requirements.txt

python manage.py collectstatic --no-input --settings=doccure_proj.settings.

python manage.py migrate --settings=doccure_proj.settings.prod

