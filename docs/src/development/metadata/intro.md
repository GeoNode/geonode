# Intro to GeoNode metadata management

## Introduction

Geographic metadata describes the content, quality, location, and structure of geospatial datasets. In GeoNode, it enables dataset discovery, interoperability, and standardized data management through structured, searchable information.

GeoNode has its own internal metadata model, originally developed to populate the most relevant elements of the ISO 19115 standard. This model supported core geospatial metadata fields and was tightly coupled with the Django backend.

With the release of GeoNode 5.x, a new metadata engine was introduced. It is based on JSON Schema, making it significantly more flexible and easier to customize. Unlike previous versions, where adding new fields required modifying the Django data model, developers can now define and extend metadata structures through configurable schemas without touching the core database structure.

## Design overview

The metadata engine, implemented since GeoNode 5, is based on a JSON Schema-driven model, offering a flexible and extensible way to manage resource metadata.

Core concepts:

- JSON Schema Model

    A single JSON Schema defines the structure, validation, and UI behavior of metadata fields across all resources, for example datasets and maps.

    The full set of metadata is passed as input and output, fully respecting the JSON Schema instance specifications, ensuring strict compliance with the defined structure.

- Dynamic UI Generation

    The frontend generates metadata forms dynamically based on the schema, including field types, labels, grouping, and constraints.

- Data Storage

    Core metadata fields, for example title, abstract, and category, are still stored in the traditional `ResourceBase` model.

    Custom or extended fields are stored using a new *Sparse field* mechanism, allowing flexible, schema-driven metadata extension without altering the database schema.

- Validation & Localization

    Input is validated against the JSON Schema, and schemas support multilingual labels and descriptions, enabling internationalized forms.
