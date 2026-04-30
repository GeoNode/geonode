# Schema caching

The JSON Schema is requested and used very often when dealing with metadata: the client requests the schema every time the metadata editor is opened, and the metadata manager uses the schema both when creating and receiving an instance.

Generating the JSON Schema may be a bit heavy on the backend, so there is a caching mechanism that holds a built schema for every language. Remember that field labels and descriptions are also inside the JSON schema, and different languages may have different labels.

The JSONSchema structure is usually fixed, so the cache should be expunged only when there are changes in the labels. There are mechanisms, based on the label thesaurus date, that force the different workers to recreate the schema when labels change.
