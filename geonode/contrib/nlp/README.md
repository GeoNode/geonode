# NLP Contrib App

NLP is a contrib app starting with GeoNode 2.4.  The nlp contrib app uses [MITIE](https://github.com/mit-nlp/MITIE) and natural language processing (NLP) techniques to infer additional metadata from the raw contents of new text documents and metadata xml uploaded with shapefiles.  This contrib app helps fill key metadata gaps.

## Settings

### Activation

To activate the nlp contrib app, you need to add `geonode.contrib.nlp` to `INSTALLED_APPS`.  For example, with:

```Python
GEONODE_CONTRIB_APPS = (
    'geonode.contrib.nlp'
)
GEONODE_APPS = GEONODE_APPS + GEONODE_CONTRIB_APPS
```

### Configuration

The relevant section in [settings.py](https://github.com/GeoNode/geonode/blob/master/geonode/settings.py) starts at line [806](https://github.com/GeoNode/geonode/blob/master/geonode/settings.py#L806).
```Python
# Settings for NLP contrib app
NLP_ENABLED = False
NLP_LOCATION_THRESHOLD = 1.0
NLP_LIBRARY_PATH = "/opt/MITIE/mitielib"
NLP_MODEL_PATH = "/opt/MITIE/MITIE-models/english/ner_model.dat"
```

To enable the nlp contrib app switch `NLP_ENABLED` to `True` and replace the existing `NLP_LIBRARY_PATH` and `NLP_MODEL_PATH` with the relevant paths.  `NLP_LIBRARY_PATH` points to the MITIE library folder.  `NLP_MODEL_PATH` points to the Named Entity Recognizer (NER) you will use to parse text.  The basic NER model is for English.  There's also a pre-built spanish version.  You can learn more at https://github.com/mit-nlp/MITIE/wiki/Evaluation.  You can train your own model, too; however, that requires a significant investment.  You can use https://github.com/Sotera/mitie-trainer or a command line workflow.  As new language models are built for MITIE, GeoNode should be able to cover multiple languages.

## MITIE

From MITIE's README:

*This project provides free (even for commercial use) state-of-the-art information extraction tools. The current release includes tools for performing named entity extraction and binary relation detection as well as tools for training custom extractors and relation detectors.*

*MITIE comes with trained models for English and Spanish. The English named entity recognition model is trained based on data from the English Gigaword news corpus, the CoNLL 2003 named entity recognition task, and ACE data. The Spanish model is based on the Spanish Gigaword corpus and CoNLL 2002 named entity recognition task. There are also 21 English binary relation extraction models provided which were trained on a combination of Wikipedia and Freebase data.*
