# Notes on Layer styling


- Classify request arrives via API Endpoint with the following params:
    datafile_id = models.IntegerField()
    dataverse_installation_name = models.CharField(max_length=255)
    layer_name = models.CharField(max_length=255)
    attribute = models.CharField(max_length=255)
    intervals = models.IntegerField()
    method = models.CharField(max_length=255)
    ramp = models.CharField(max_length=255)
    startColor = models.CharField(max_length=30)
    endColor = models.CharField(max_length=30)
    reverse = models.BooleanField(default=False)

## StyleOrganizer (dataverse_connect/style_organizer.py)

Wrapper class to process Classify params through 3 processes:

    1.  Generate SLD Rules
    2.  Format Rules into a full SLD
    3.  Add new SLD to Layer


## 1. Generate SLD Rules


- Check and format the style parameters sent via the API
  - **ClassifyRequestDataForm**: ```from shared_dataverse_information.layer_classification.forms_api import ClassifyRequestDataForm```
  
- Example input:
    ```json
    {
        "layer_name": "social_disorder_shapefile_zip_x7x",
        "dataverse_installation_name": "http://localhost:8000",
        "datafile_id": 7775,
        "endColor": "#08306b",
        "intervals": 5,
        "attribute": "SocStrif_1",
        "method": "equalInterval",
        "ramp": "Blue",
        "startColor": "#f7fbff",
        "reverse": false
    }
    ```
