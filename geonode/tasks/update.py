from celery.task import task
from geonode.geoserver.helpers import gs_slurp
from geonode.documents.models import Document
from geonode.cephgeo.models import CephDataObject, DataClassification
import geonode.cephgeo.utils


@task(name='geonode.tasks.ceph_metadata_udate', queue='update')
def ceph_metadata_udate(uploaded_objects):
    """
        NOTE: DOES NOT WORK
          Outputs error 'OperationalError: database is locked'
          Need a better way of making celery write into the database
    """
    #Save each ceph object
    for obj_meta_dict in uploaded_objects:
        ceph_obj = CephDataObject(  name = obj_meta_dict['name'],
                                    #last_modified = time.strptime(obj_meta_dict['last_modified'], "%Y-%m-%d %H:%M:%S"),
                                    last_modified = obj_meta_dict['last_modified'],
                                    size_in_bytes = obj_meta_dict['bytes'],
                                    content_type = obj_meta_dict['content_type'],
                                    data_class = DataClassification.get_class_from_filename(obj_meta_dict['name']),
                                    file_hash = obj_meta_dict['hash'],
                                    grid_ref = obj_meta_dict['grid_ref'])
        ceph_obj.save()

@task(name='geonode.tasks.update.geoserver_update_layers', queue='update')
def geoserver_update_layers(*args, **kwargs):
    """
    Runs update layers.
    """
    return gs_slurp(*args, **kwargs)


@task(name='geonode.tasks.update.create_document_thumbnail', queue='update')
def create_document_thumbnail(object_id):
    """
    Runs the create_thumbnail logic on a document.
    """

    try:
        document = Document.objects.get(id=object_id)

    except Document.DoesNotExist:
        return

    image = document._render_thumbnail()
    filename = 'doc-%s-thumb.png' % document.id
    document.save_thumbnail(filename, image)
