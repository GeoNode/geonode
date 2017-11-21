# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0028_resourcebase_is_approved'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcebase',
            name='language',
            field=models.CharField(default=b'eng', help_text='language used within the dataset', max_length=3, verbose_name='language', choices=[(b'abk', b'Abkhazian'), (b'aar', b'Afar'), (b'afr', b'Afrikaans'), (b'amh', b'Amharic'), (b'ara', b'Arabic'), (b'asm', b'Assamese'), (b'aym', b'Aymara'), (b'aze', b'Azerbaijani'), (b'bak', b'Bashkir'), (b'ben', b'Bengali'), (b'bih', b'Bihari'), (b'bis', b'Bislama'), (b'bre', b'Breton'), (b'bul', b'Bulgarian'), (b'bel', b'Byelorussian'), (b'cat', b'Catalan'), (b'cos', b'Corsican'), (b'dan', b'Danish'), (b'dzo', b'Dzongkha'), (b'eng', b'English'), (b'fra', b'French'), (b'epo', b'Esperanto'), (b'est', b'Estonian'), (b'fao', b'Faroese'), (b'fij', b'Fijian'), (b'fin', b'Finnish'), (b'fry', b'Frisian'), (b'glg', b'Gallegan'), (b'ger', b'German'), (b'gre', b'Greek'), (b'kal', b'Greenlandic'), (b'grn', b'Guarani'), (b'guj', b'Gujarati'), (b'hau', b'Hausa'), (b'heb', b'Hebrew'), (b'hin', b'Hindi'), (b'hun', b'Hungarian'), (b'ind', b'Indonesian'), (b'ina', b'Interlingua (International Auxiliary language Association)'), (b'iku', b'Inuktitut'), (b'ipk', b'Inupiak'), (b'ita', b'Italian'), (b'jpn', b'Japanese'), (b'kan', b'Kannada'), (b'kas', b'Kashmiri'), (b'kaz', b'Kazakh'), (b'khm', b'Khmer'), (b'kin', b'Kinyarwanda'), (b'kir', b'Kirghiz'), (b'kor', b'Korean'), (b'kur', b'Kurdish'), (b'oci', b"Langue d 'Oc (post 1500)"), (b'lao', b'Lao'), (b'lat', b'Latin'), (b'lav', b'Latvian'), (b'lin', b'Lingala'), (b'lit', b'Lithuanian'), (b'mlg', b'Malagasy'), (b'mlt', b'Maltese'), (b'mar', b'Marathi'), (b'mol', b'Moldavian'), (b'mon', b'Mongolian'), (b'nau', b'Nauru'), (b'nep', b'Nepali'), (b'nor', b'Norwegian'), (b'ori', b'Oriya'), (b'orm', b'Oromo'), (b'pan', b'Panjabi'), (b'pol', b'Polish'), (b'por', b'Portuguese'), (b'pus', b'Pushto'), (b'que', b'Quechua'), (b'roh', b'Rhaeto-Romance'), (b'run', b'Rundi'), (b'rus', b'Russian'), (b'smo', b'Samoan'), (b'sag', b'Sango'), (b'san', b'Sanskrit'), (b'scr', b'Serbo-Croatian'), (b'sna', b'Shona'), (b'snd', b'Sindhi'), (b'sin', b'Singhalese'), (b'ssw', b'Siswant'), (b'slv', b'Slovenian'), (b'som', b'Somali'), (b'sot', b'Sotho'), (b'spa', b'Spanish'), (b'sun', b'Sudanese'), (b'swa', b'Swahili'), (b'tgl', b'Tagalog'), (b'tgk', b'Tajik'), (b'tam', b'Tamil'), (b'tat', b'Tatar'), (b'tel', b'Telugu'), (b'tha', b'Thai'), (b'tir', b'Tigrinya'), (b'tog', b'Tonga (Nyasa)'), (b'tso', b'Tsonga'), (b'tsn', b'Tswana'), (b'tur', b'Turkish'), (b'tuk', b'Turkmen'), (b'twi', b'Twi'), (b'uig', b'Uighur'), (b'ukr', b'Ukrainian'), (b'urd', b'Urdu'), (b'uzb', b'Uzbek'), (b'vie', b'Vietnamese'), (b'vol', b'Volap\xc3\xbck'), (b'wol', b'Wolof'), (b'xho', b'Xhosa'), (b'yid', b'Yiddish'), (b'yor', b'Yoruba'), (b'zha', b'Zhuang'), (b'zul', b'Zulu')]),
        ),
    ]
