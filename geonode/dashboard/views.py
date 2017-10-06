import tempfile
import os
import tarfile
import shutil

from urlparse import urlparse

from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render

from geonode import settings
from forms import DataFolderBackupForm


def metadatabackup(request):
    """
    This view is for database metadata backup.
    Only super admin can do the job
    :return:
    """
    if request.user.is_superuser:
        database_name = settings.DATABASES['default']['NAME']
        database_user = settings.DATABASES['default']['USER']
        database_password = settings.DATABASES['default']['PASSWORD']
        database_host = settings.DATABASES['default']['HOST']
        database_port = settings.DATABASES['default']['PORT']


        tempdir = tempfile.mkdtemp()
        #command_string = 'echo ' + sudo_pass + ' | sudo -S  -u postgres -i pg_dump -c -Fc ' + database_name +' > ' + tempdir + '/metadata.backup'
        command_string = 'pg_dump -h' + database_host + ' -p' + database_port + ' -U' + database_user + ' -c -Fc -w ' +\
                         database_name + ' > ' + tempdir +'/metadata.backup'
        os.putenv("PGPASSWORD", database_password)
        os.system(command_string)
        file_path = tempdir + '/metadata.backup'
        fsock = open(file_path,"rb")
        response = HttpResponse(fsock, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=metadata.backup'
        if tempdir is not None:
            shutil.rmtree(tempdir)
        return response
    else:
        return Http404("You dont have permission")


def databackup(request):
    """
    This view is for database data backup.
    Only super admin can do the job
    :return:
    """
    if request.user.is_superuser:
        database_name = settings.DATABASES['datastore']['NAME']
        database_user = settings.DATABASES['datastore']['USER']
        database_password = settings.DATABASES['datastore']['PASSWORD']
        database_host = str(settings.DATABASES['datastore']['HOST'])
        database_port = str(settings.DATABASES['datastore']['PORT'])

        tempdir = tempfile.mkdtemp()
        command_string = 'pg_dump -h' + database_host + ' -p' + database_port + ' -U' + database_user + ' -c -Fc -w ' +\
                         database_name + ' > ' + tempdir +'/data.backup'
        #command_string = 'echo ' + sudo_pass + ' | sudo -S  -u postgres -i pg_dump -c -Fc ' + database_name +' > ' + tempdir + '/data.backup'
        os.putenv("PGPASSWORD", database_password)
        os.system(command_string)
        file_path = tempdir + '/data.backup'
        fsock = open(file_path,"rb")
        response = HttpResponse(fsock, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=data.backup'
        if tempdir is not None:
            shutil.rmtree(tempdir)
        return response
    else:
        return Http404('You dont have permission')


def uploadedFolderBackup(request):
    if request.user.is_superuser and request.user.is_authenticated():
        response = HttpResponse(content_type='application/x-gzip')
        response['Content-Disposition'] = 'attachment; filename=media_backup.tar.gz'
        tarred = tarfile.open(fileobj=response, mode='w:gz')
        tarred.add(settings.MEDIA_ROOT)
        tarred.close()
        return response
    else:
        return Http404("You dont have permission to perform this job.")


def geoserverDataFolderBackup(request):
    if request.method == 'POST':
        if request.user.is_superuser and request.user.is_authenticated():
            form = DataFolderBackupForm(request.POST)
            if form.is_valid():
                tempdir = settings.TEMP_DIR
                os.system('mkdir ' + tempdir)
                host_user = form.cleaned_data['user']
                host = urlparse(settings.OGC_SERVER['default']['LOCATION']).hostname
                password = form.cleaned_data['password']
                form = DataFolderBackupForm()
                # sshpass -p "Geodash@bcc@world@123" scp -r  root@103.48.16.34:/home/geodash/geodash_200/geodash/geonode/maps /home/jaha/Music
                command_string = 'sshpass -p ' + password + ' scp -r  '+host_user+'@'+host+':/var/lib/tomcat7/webapps/geoserver/data '+ tempdir
                os.system(command_string)

                response = HttpResponse(content_type='application/x-gzip')
                response['Content-Disposition'] = 'attachment; filename=data_backup.tar.gz'
                tarred = tarfile.open(fileobj=response, mode='w:gz')
                tarred.add(tempdir)
                tarred.close()
                if tempdir is not None:
                    shutil.rmtree(tempdir)
                return response

        else:
            return Http404("You dont have permission to perform this job.")

    else:
        form = DataFolderBackupForm()

    return render(request, "data_backup.html", {'form': form, })
