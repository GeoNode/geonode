from django.contrib.auth.models import User
u = User.objects.get(username='replace.me.admin.user')
u.set_password('replace.me.admin.pw')
u.save()
