# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.utils.timezone
import geonode.people.models
import django.core.validators
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=30, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, verbose_name='username')),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('email', models.EmailField(max_length=254, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('organization', models.CharField(help_text='name of the responsible organization', max_length=255, null=True, verbose_name='Organization Name', blank=True)),
                ('profile', models.TextField(help_text='introduce yourself', null=True, verbose_name='Profile', blank=True)),
                ('position', models.CharField(help_text='role or position of the responsible person', max_length=255, null=True, verbose_name='Position Name', blank=True)),
                ('voice', models.CharField(help_text='telephone number by which individuals can speak to the responsible organization or individual', max_length=255, null=True, verbose_name='Voice', blank=True)),
                ('fax', models.CharField(help_text='telephone number of a facsimile machine for the responsible organization or individual', max_length=255, null=True, verbose_name='Facsimile', blank=True)),
                ('delivery', models.CharField(help_text='physical and email address at which the organization or individual may be contacted', max_length=255, null=True, verbose_name='Delivery Point', blank=True)),
                ('city', models.CharField(help_text='city of the location', max_length=255, null=True, verbose_name='City', blank=True)),
                ('area', models.CharField(help_text='state, province of the location', max_length=255, null=True, verbose_name='Administrative Area', blank=True)),
                ('zipcode', models.CharField(help_text='ZIP or other postal code', max_length=255, null=True, verbose_name='Postal Code', blank=True)),
                ('country', models.CharField(blank=True, max_length=3, null=True, help_text='country of the physical address', choices=[('AFG','Afghanistan'), ('ALA','Aland Islands'), ('ALB','Albania'), ('DZA','Algeria'), ('ASM','American Samoa'), ('AND','Andorra'), ('AGO','Angola'), ('AIA','Anguilla'), ('ATG','Antigua and Barbuda'), ('ARG','Argentina'), ('ARM','Armenia'), ('ABW','Aruba'), ('AUS','Australia'), ('AUT','Austria'), ('AZE','Azerbaijan'), ('BHS','Bahamas'), ('BHR','Bahrain'), ('BGD','Bangladesh'), ('BRB','Barbados'), ('BLR','Belarus'), ('BEL','Belgium'), ('BLZ','Belize'), ('BEN','Benin'), ('BMU','Bermuda'), ('BTN','Bhutan'), ('BOL','Bolivia'), ('BIH','Bosnia and Herzegovina'), ('BWA','Botswana'), ('BRA','Brazil'), ('VGB','British Virgin Islands'), ('BRN','Brunei Darussalam'), ('BGR','Bulgaria'), ('BFA','Burkina Faso'), ('BDI','Burundi'), ('KHM','Cambodia'), ('CMR','Cameroon'), ('CAN','Canada'), ('CPV','Cape Verde'), ('CYM','Cayman Islands'), ('CAF','Central African Republic'), ('TCD','Chad'), ('CIL','Channel Islands'), ('CHL','Chile'), ('CHN','China'), ('HKG','China - Hong Kong'), ('MAC','China - Macao'), ('COL','Colombia'), ('COM','Comoros'), ('COG','Congo'), ('COK','Cook Islands'), ('CRI','Costa Rica'), ('CIV', b"Cote d'Ivoire"), ('HRV','Croatia'), ('CUB','Cuba'), ('CYP','Cyprus'), ('CZE','Czech Republic'), ('PRK', b"Democratic People's Republic of Korea"), ('COD','Democratic Republic of the Congo'), ('DNK','Denmark'), ('DJI','Djibouti'), ('DMA','Dominica'), ('DOM','Dominican Republic'), ('ECU','Ecuador'), ('EGY','Egypt'), ('SLV','El Salvador'), ('GNQ','Equatorial Guinea'), ('ERI','Eritrea'), ('EST','Estonia'), ('ETH','Ethiopia'), ('FRO','Faeroe Islands'), ('FLK','Falkland Islands (Malvinas)'), ('FJI','Fiji'), ('FIN','Finland'), ('FRA','France'), ('GUF','French Guiana'), ('PYF','French Polynesia'), ('GAB','Gabon'), ('GMB','Gambia'), ('GEO','Georgia'), ('DEU','Germany'), ('GHA','Ghana'), ('GIB','Gibraltar'), ('GRC','Greece'), ('GRL','Greenland'), ('GRD','Grenada'), ('GLP','Guadeloupe'), ('GUM','Guam'), ('GTM','Guatemala'), ('GGY','Guernsey'), ('GIN','Guinea'), ('GNB','Guinea-Bissau'), ('GUY','Guyana'), ('HTI','Haiti'), ('VAT','Holy See (Vatican City)'), ('HND','Honduras'), ('HUN','Hungary'), ('ISL','Iceland'), ('IND','India'), ('IDN','Indonesia'), ('IRN','Iran'), ('IRQ','Iraq'), ('IRL','Ireland'), ('IMN','Isle of Man'), ('ISR','Israel'), ('ITA','Italy'), ('JAM','Jamaica'), ('JPN','Japan'), ('JEY','Jersey'), ('JOR','Jordan'), ('KAZ','Kazakhstan'), ('KEN','Kenya'), ('KIR','Kiribati'), ('KWT','Kuwait'), ('KGZ','Kyrgyzstan'), ('LAO', b"Lao People's Democratic Republic"), ('LVA','Latvia'), ('LBN','Lebanon'), ('LSO','Lesotho'), ('LBR','Liberia'), ('LBY','Libyan Arab Jamahiriya'), ('LIE','Liechtenstein'), ('LTU','Lithuania'), ('LUX','Luxembourg'), ('MKD','Macedonia'), ('MDG','Madagascar'), ('MWI','Malawi'), ('MYS','Malaysia'), ('MDV','Maldives'), ('MLI','Mali'), ('MLT','Malta'), ('MHL','Marshall Islands'), ('MTQ','Martinique'), ('MRT','Mauritania'), ('MUS','Mauritius'), ('MYT','Mayotte'), ('MEX','Mexico'), ('FSM','Micronesia, Federated States of'), ('MCO','Monaco'), ('MNG','Mongolia'), ('MNE','Montenegro'), ('MSR','Montserrat'), ('MAR','Morocco'), ('MOZ','Mozambique'), ('MMR','Myanmar'), ('NAM','Namibia'), ('NRU','Nauru'), ('NPL','Nepal'), ('NLD','Netherlands'), ('ANT','Netherlands Antilles'), ('NCL','New Caledonia'), ('NZL','New Zealand'), ('NIC','Nicaragua'), ('NER','Niger'), ('NGA','Nigeria'), ('NIU','Niue'), ('NFK','Norfolk Island'), ('MNP','Northern Mariana Islands'), ('NOR','Norway'), ('PSE','Occupied Palestinian Territory'), ('OMN','Oman'), ('PAK','Pakistan'), ('PLW','Palau'), ('PAN','Panama'), ('PNG','Papua New Guinea'), ('PRY','Paraguay'), ('PER','Peru'), ('PHL','Philippines'), ('PCN','Pitcairn'), ('POL','Poland'), ('PRT','Portugal'), ('PRI','Puerto Rico'), ('QAT','Qatar'), ('KOR','Republic of Korea'), ('MDA','Republic of Moldova'), ('REU','Reunion'), ('ROU','Romania'), ('RUS','Russian Federation'), ('RWA','Rwanda'), ('BLM','Saint-Barthelemy'), ('SHN','Saint Helena'), ('KNA','Saint Kitts and Nevis'), ('LCA','Saint Lucia'), ('MAF','Saint-Martin (French part)'), ('SPM','Saint Pierre and Miquelon'), ('VCT','Saint Vincent and the Grenadines'), ('WSM','Samoa'), ('SMR','San Marino'), ('STP','Sao Tome and Principe'), ('SAU','Saudi Arabia'), ('SEN','Senegal'), ('SRB','Serbia'), ('SYC','Seychelles'), ('SLE','Sierra Leone'), ('SGP','Singapore'), ('SVK','Slovakia'), ('SVN','Slovenia'), ('SLB','Solomon Islands'), ('SOM','Somalia'), ('ZAF','South Africa'), ('SSD','South Sudan'), ('ESP','Spain'), ('LKA','Sri Lanka'), ('SDN','Sudan'), ('SUR','Suriname'), ('SJM','Svalbard and Jan Mayen Islands'), ('SWZ','Swaziland'), ('SWE','Sweden'), ('CHE','Switzerland'), ('SYR','Syrian Arab Republic'), ('TJK','Tajikistan'), ('THA','Thailand'), ('TLS','Timor-Leste'), ('TGO','Togo'), ('TKL','Tokelau'), ('TON','Tonga'), ('TTO','Trinidad and Tobago'), ('TUN','Tunisia'), ('TUR','Turkey'), ('TKM','Turkmenistan'), ('TCA','Turks and Caicos Islands'), ('TUV','Tuvalu'), ('UGA','Uganda'), ('UKR','Ukraine'), ('ARE','United Arab Emirates'), ('GBR','United Kingdom'), ('TZA','United Republic of Tanzania'), ('USA','United States of America'), ('VIR','United States Virgin Islands'), ('URY','Uruguay'), ('UZB','Uzbekistan'), ('VUT','Vanuatu'), ('VEN','Venezuela (Bolivarian Republic of)'), ('VNM','Viet Nam'), ('WLF','Wallis and Futuna Islands'), ('ESH','Western Sahara'), ('YEM','Yemen'), ('ZMB','Zambia'), ('ZWE','Zimbabwe')])),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('keywords', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject             (space or comma-separated', verbose_name='keywords')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                ('objects', geonode.people.models.ProfileUserManager()),
            ],
        ),
    ]
