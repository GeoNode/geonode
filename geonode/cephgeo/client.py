import swiftclient, warnings, os, mimetypes, logging
from pprint import pprint
from os import listdir
from os.path import isfile, join


original_filters = warnings.filters[:]

# Ignore warnings.
warnings.simplefilter("ignore")

#~ try:
    #~ pass
#~ finally:
    #~ warnings.filters = original_filters
    
class CephStorageClient(object):
    
    def __init__(self, user, key, ceph_radosgw_url, container_name=None):
        self.user = user
            
        self.key = key
        
        self.ceph_radosgw_url = ceph_radosgw_url
        
        self.connection = self.__connect()
        
        self.active_container_name = container_name
        
        self.log = self.log_wrapper()

    
    def __connect(self):
        return swiftclient.Connection(
            user=self.user,
            key=self.key,
            authurl=self.ceph_radosgw_url+"/auth",
            insecure=True,
        )
    
    def list_containers(self):
        pprint(self.connection.get_account()[1])
        return list(self.connection.get_account()[1])
    
    def set_active_container(self, container_name):
        self.active_container_name =  container_name
    
    def get_active_container(self):
        return self.active_container_name
    
    def list_files(self, container_name=None):
        if container_name is not None:
            return list(self.connection.get_container(container_name)[1])
        else:
            return list(self.connection.get_container(self.active_container_name)[1])
    
    def delete_object(self, object_name, container=None):
        if container is None:
            container = self.active_container_name
        self.connection.delete_object( container, 
                                        object_name)

    def upload_file_from_path(self, file_path, container=None):
        file_name = os.path.basename(file_path)
        if container is None:
            container = self.active_container_name
        #file_id_name = file_name.split(".")[0]
        
        content_type="None"
        try:
            content_type = mimetypes.types_map["."+file_name.split(".")[-1]]
        
        except KeyError:
            pass
        
        self.log.info("Uploading  file {0} [size:{1} | type:{2}]...".format( file_name,
                                                                        os.stat(file_path).st_size,
                                                                        content_type))
        with open(file_path, 'r') as file_obj:
            self.connection.put_object( container, 
                                        file_name,
                                        contents=file_obj.read(),
                                        content_type=content_type)
        
    
    def upload_via_http(self):
        pass
    
    def download_file_to_path(self, object_name, destination_path, container=None):
        obj_tuple = self.connection.get_object(self.active_container_name, object_name)
        file_path = join(destination_path,object_name)
        if container is None:
            container = self.active_container_name
            
        with open(file_path, 'w') as dl_file:
                dl_file.write(obj_tuple[1])
                
        self.log.info("Finished downloading to [{0}]. Wrote [{1}] bytes...".format(  file_path,
                                                                                os.stat(file_path).st_size,))
    
    def download_via_http(self):
        pass
    
    def close_connection(self):
        self.connection.close()
    
    def get_cwd(self):
        """
            Returns the current working directory of the python script
        """
        path = os.path.realpath(__file__)
        if "?" in path:
            return path.rpartition("?")[0].rpartition("/")[0]+"/"
        else:
            return path.rpartition("/")[0]+"/"
    
    def log_wrapper(self):
        """
        Wrapper to set logging parameters for output
        """
        # Initialize logging
        logging.basicConfig(filename=self.get_cwd()+'logs/ceph_storage.log',level=logging.DEBUG)
        self.LOGGING = True
        log = logging.getLogger('client.py')
        
        # Set the log format and log level
        log.setLevel(logging.DEBUG)
        #log.setLevel(logging.INFO)

        # Set the log format.
        stream = logging.StreamHandler()
        logformat = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%b %d %H:%M:%S')
        stream.setFormatter(logformat)

        log.addHandler(stream)
        return log
