from geonode.layers.models import Layer

def list_duplicate_layer():
    uniq = set()
    dups = []
    for x in Layer.objects.all():
        if x.typename in uniq:
            dups.append(x)
        uniq.add(x.typename)
    return dups

def write_to_txt(writethislist,filename = 'duplicatelayers.txt'):
    with open(filename,'w') as f:
        try:
            f.write('\n'.join(writethislist))
        except Exception as e:
            f.write(e)

if __name__ == '__main__':
    if sys.argv:
        write_to_txt(list_duplicate_layer,sys.argv[0]) #will get the first argument as filename
    else:
        write_to_txt(list_duplicate_layer)
