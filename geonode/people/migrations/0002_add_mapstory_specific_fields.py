# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0001_initial'),
        ('avatar', '0001_initial'),
        ('account', '0001_initial'),
    ]

    run_before = [
        # ('notification', '0001_initial')
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='Volunteer_Technical_Community',
            field=models.BooleanField(default=False, help_text='indicates membership of the Volunteer Technical Comunity', verbose_name='Volunteer Technical Community'),
        ),
        migrations.AddField(
            model_name='profile',
            name='avatar_100',
            field=models.CharField(max_length=512, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='digest',
            field=models.BooleanField(default=False, help_text='Subscribe to MapStory monthly email digest', verbose_name='Monthly email digest'),
        ),
        migrations.AddField(
            model_name='profile',
            name='education',
            field=models.TextField(help_text='Provide some details about your Education and Background', null=True, verbose_name='Education', blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='expertise',
            field=models.TextField(help_text='Provide some details about your Expertise', null=True, verbose_name='Expertise', blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='social_facebook',
            field=models.CharField(help_text='Provide your Facebook handle or URL', max_length=255, null=True, verbose_name='Facebook Profile', blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='social_github',
            field=models.CharField(help_text='Provide your GitHub handle or URL', max_length=255, null=True, verbose_name='GitHub Profile', blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='social_linkedin',
            field=models.CharField(help_text='Provide your LinkedIn handle or URL', max_length=255, null=True, verbose_name='LinkedIn Profile', blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='social_twitter',
            field=models.CharField(help_text='Provide your Twitter handle or URL', max_length=255, null=True, verbose_name='Twitter Handle', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='city',
            field=models.CharField(help_text='What city do you spend most of your time in?', max_length=255, null=True, verbose_name='City', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='country',
            field=models.CharField(blank=True, max_length=3, null=True, help_text='What country do you spend most of your time in?', choices=[(b'AFG', b'Afghanistan'), (b'ALA', b'Aland Islands'), (b'ALB', b'Albania'), (b'DZA', b'Algeria'), (b'ASM', b'American Samoa'), (b'AND', b'Andorra'), (b'AGO', b'Angola'), (b'AIA', b'Anguilla'), (b'ATG', b'Antigua and Barbuda'), (b'ARG', b'Argentina'), (b'ARM', b'Armenia'), (b'ABW', b'Aruba'), (b'AUS', b'Australia'), (b'AUT', b'Austria'), (b'AZE', b'Azerbaijan'), (b'BHS', b'Bahamas'), (b'BHR', b'Bahrain'), (b'BGD', b'Bangladesh'), (b'BRB', b'Barbados'), (b'BLR', b'Belarus'), (b'BEL', b'Belgium'), (b'BLZ', b'Belize'), (b'BEN', b'Benin'), (b'BMU', b'Bermuda'), (b'BTN', b'Bhutan'), (b'BOL', b'Bolivia'), (b'BIH', b'Bosnia and Herzegovina'), (b'BWA', b'Botswana'), (b'BRA', b'Brazil'), (b'VGB', b'British Virgin Islands'), (b'BRN', b'Brunei Darussalam'), (b'BGR', b'Bulgaria'), (b'BFA', b'Burkina Faso'), (b'BDI', b'Burundi'), (b'KHM', b'Cambodia'), (b'CMR', b'Cameroon'), (b'CAN', b'Canada'), (b'CPV', b'Cape Verde'), (b'CYM', b'Cayman Islands'), (b'CAF', b'Central African Republic'), (b'TCD', b'Chad'), (b'CIL', b'Channel Islands'), (b'CHL', b'Chile'), (b'CHN', b'China'), (b'HKG', b'China - Hong Kong'), (b'MAC', b'China - Macao'), (b'COL', b'Colombia'), (b'COM', b'Comoros'), (b'COG', b'Congo'), (b'COK', b'Cook Islands'), (b'CRI', b'Costa Rica'), (b'CIV', b"Cote d'Ivoire"), (b'HRV', b'Croatia'), (b'CUB', b'Cuba'), (b'CYP', b'Cyprus'), (b'CZE', b'Czech Republic'), (b'PRK', b"Democratic People's Republic of Korea"), (b'COD', b'Democratic Republic of the Congo'), (b'DNK', b'Denmark'), (b'DJI', b'Djibouti'), (b'DMA', b'Dominica'), (b'DOM', b'Dominican Republic'), (b'ECU', b'Ecuador'), (b'EGY', b'Egypt'), (b'SLV', b'El Salvador'), (b'GNQ', b'Equatorial Guinea'), (b'ERI', b'Eritrea'), (b'EST', b'Estonia'), (b'ETH', b'Ethiopia'), (b'FRO', b'Faeroe Islands'), (b'FLK', b'Falkland Islands (Malvinas)'), (b'FJI', b'Fiji'), (b'FIN', b'Finland'), (b'FRA', b'France'), (b'GUF', b'French Guiana'), (b'PYF', b'French Polynesia'), (b'GAB', b'Gabon'), (b'GMB', b'Gambia'), (b'GEO', b'Georgia'), (b'DEU', b'Germany'), (b'GHA', b'Ghana'), (b'GIB', b'Gibraltar'), (b'GRC', b'Greece'), (b'GRL', b'Greenland'), (b'GRD', b'Grenada'), (b'GLP', b'Guadeloupe'), (b'GUM', b'Guam'), (b'GTM', b'Guatemala'), (b'GGY', b'Guernsey'), (b'GIN', b'Guinea'), (b'GNB', b'Guinea-Bissau'), (b'GUY', b'Guyana'), (b'HTI', b'Haiti'), (b'VAT', b'Holy See (Vatican City)'), (b'HND', b'Honduras'), (b'HUN', b'Hungary'), (b'ISL', b'Iceland'), (b'IND', b'India'), (b'IDN', b'Indonesia'), (b'IRN', b'Iran'), (b'IRQ', b'Iraq'), (b'IRL', b'Ireland'), (b'IMN', b'Isle of Man'), (b'ISR', b'Israel'), (b'ITA', b'Italy'), (b'JAM', b'Jamaica'), (b'JPN', b'Japan'), (b'JEY', b'Jersey'), (b'JOR', b'Jordan'), (b'KAZ', b'Kazakhstan'), (b'KEN', b'Kenya'), (b'KIR', b'Kiribati'), (b'KWT', b'Kuwait'), (b'KGZ', b'Kyrgyzstan'), (b'LAO', b"Lao People's Democratic Republic"), (b'LVA', b'Latvia'), (b'LBN', b'Lebanon'), (b'LSO', b'Lesotho'), (b'LBR', b'Liberia'), (b'LBY', b'Libyan Arab Jamahiriya'), (b'LIE', b'Liechtenstein'), (b'LTU', b'Lithuania'), (b'LUX', b'Luxembourg'), (b'MKD', b'Macedonia'), (b'MDG', b'Madagascar'), (b'MWI', b'Malawi'), (b'MYS', b'Malaysia'), (b'MDV', b'Maldives'), (b'MLI', b'Mali'), (b'MLT', b'Malta'), (b'MHL', b'Marshall Islands'), (b'MTQ', b'Martinique'), (b'MRT', b'Mauritania'), (b'MUS', b'Mauritius'), (b'MYT', b'Mayotte'), (b'MEX', b'Mexico'), (b'FSM', b'Micronesia, Federated States of'), (b'MCO', b'Monaco'), (b'MNG', b'Mongolia'), (b'MNE', b'Montenegro'), (b'MSR', b'Montserrat'), (b'MAR', b'Morocco'), (b'MOZ', b'Mozambique'), (b'MMR', b'Myanmar'), (b'NAM', b'Namibia'), (b'NRU', b'Nauru'), (b'NPL', b'Nepal'), (b'NLD', b'Netherlands'), (b'ANT', b'Netherlands Antilles'), (b'NCL', b'New Caledonia'), (b'NZL', b'New Zealand'), (b'NIC', b'Nicaragua'), (b'NER', b'Niger'), (b'NGA', b'Nigeria'), (b'NIU', b'Niue'), (b'NFK', b'Norfolk Island'), (b'MNP', b'Northern Mariana Islands'), (b'NOR', b'Norway'), (b'PSE', b'Occupied Palestinian Territory'), (b'OMN', b'Oman'), (b'PAK', b'Pakistan'), (b'PLW', b'Palau'), (b'PAN', b'Panama'), (b'PNG', b'Papua New Guinea'), (b'PRY', b'Paraguay'), (b'PER', b'Peru'), (b'PHL', b'Philippines'), (b'PCN', b'Pitcairn'), (b'POL', b'Poland'), (b'PRT', b'Portugal'), (b'PRI', b'Puerto Rico'), (b'QAT', b'Qatar'), (b'KOR', b'Republic of Korea'), (b'MDA', b'Republic of Moldova'), (b'REU', b'Reunion'), (b'ROU', b'Romania'), (b'RUS', b'Russian Federation'), (b'RWA', b'Rwanda'), (b'BLM', b'Saint-Barthelemy'), (b'SHN', b'Saint Helena'), (b'KNA', b'Saint Kitts and Nevis'), (b'LCA', b'Saint Lucia'), (b'MAF', b'Saint-Martin (French part)'), (b'SPM', b'Saint Pierre and Miquelon'), (b'VCT', b'Saint Vincent and the Grenadines'), (b'WSM', b'Samoa'), (b'SMR', b'San Marino'), (b'STP', b'Sao Tome and Principe'), (b'SAU', b'Saudi Arabia'), (b'SEN', b'Senegal'), (b'SRB', b'Serbia'), (b'SYC', b'Seychelles'), (b'SLE', b'Sierra Leone'), (b'SGP', b'Singapore'), (b'SVK', b'Slovakia'), (b'SVN', b'Slovenia'), (b'SLB', b'Solomon Islands'), (b'SOM', b'Somalia'), (b'ZAF', b'South Africa'), (b'SSD', b'South Sudan'), (b'ESP', b'Spain'), (b'LKA', b'Sri Lanka'), (b'SDN', b'Sudan'), (b'SUR', b'Suriname'), (b'SJM', b'Svalbard and Jan Mayen Islands'), (b'SWZ', b'Swaziland'), (b'SWE', b'Sweden'), (b'CHE', b'Switzerland'), (b'SYR', b'Syrian Arab Republic'), (b'TJK', b'Tajikistan'), (b'THA', b'Thailand'), (b'TLS', b'Timor-Leste'), (b'TGO', b'Togo'), (b'TKL', b'Tokelau'), (b'TON', b'Tonga'), (b'TTO', b'Trinidad and Tobago'), (b'TUN', b'Tunisia'), (b'TUR', b'Turkey'), (b'TKM', b'Turkmenistan'), (b'TCA', b'Turks and Caicos Islands'), (b'TUV', b'Tuvalu'), (b'UGA', b'Uganda'), (b'UKR', b'Ukraine'), (b'ARE', b'United Arab Emirates'), (b'GBR', b'United Kingdom'), (b'TZA', b'United Republic of Tanzania'), (b'USA', b'United States of America'), (b'VIR', b'United States Virgin Islands'), (b'URY', b'Uruguay'), (b'UZB', b'Uzbekistan'), (b'VUT', b'Vanuatu'), (b'VEN', b'Venezuela (Bolivarian Republic of)'), (b'VNM', b'Viet Nam'), (b'WLF', b'Wallis and Futuna Islands'), (b'ESH', b'Western Sahara'), (b'YEM', b'Yemen'), (b'ZMB', b'Zambia'), (b'ZWE', b'Zimbabwe')]),
        ),
        migrations.AlterField(
            model_name='profile',
            name='keywords',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject             (space or comma-separated', verbose_name='keywords'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='profile',
            field=models.TextField(help_text='Introduce yourself in under 200 characters', null=True, verbose_name='Profile', blank=True),
        ),
    ]
