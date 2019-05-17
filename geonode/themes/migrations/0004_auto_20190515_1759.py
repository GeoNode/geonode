# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geonode_themes', '0003_remove_geonodethemecustomization_identifier'),
    ]

    operations = [
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='body_text_color',
            field=models.CharField(default=b'#3a3a3a', max_length=10),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_accept_close_reload',
            field=models.CharField(default=b'false', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_animate_speed_hide',
            field=models.CharField(default=b'500', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_animate_speed_show',
            field=models.CharField(default=b'500', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_as_popup',
            field=models.CharField(default=b'false', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_background',
            field=models.CharField(default=b'#2c689c', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_bar_enabled',
            field=models.BooleanField(default=True, verbose_name=b'Cookies Law Info Bar'),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_bar_head',
            field=models.TextField(default=b'This website uses cookies'),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_bar_heading_text',
            field=models.CharField(default=b'This website uses cookies', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_bar_text',
            field=models.TextField(default=b'This website uses cookies to improve your experience,         check <strong><a style="color:#000000" href="/privacy_cookies/">this page</a></strong> for details.         We\'ll assume you\'re ok with this, but you can opt-out if you wish.'),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_border',
            field=models.CharField(default=b'#444', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_border_on',
            field=models.CharField(default=b'false', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_1_as_button',
            field=models.CharField(default=b'true', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_1_button_colour',
            field=models.CharField(default=b'#000', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_1_button_hover',
            field=models.CharField(default=b'#000000', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_1_link_colour',
            field=models.CharField(default=b'#2c689c', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_1_new_win',
            field=models.CharField(default=b'true', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_2_as_button',
            field=models.CharField(default=b'true', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_2_button_colour',
            field=models.CharField(default=b'#000000', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_2_button_hover',
            field=models.CharField(default=b'#000000', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_2_hidebar',
            field=models.CharField(default=b'true', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_2_link_colour',
            field=models.CharField(default=b'#2c689c', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_3_as_button',
            field=models.CharField(default=b'true', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_3_button_colour',
            field=models.CharField(default=b'#000', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_3_button_hover',
            field=models.CharField(default=b'#000000', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_3_link_colour',
            field=models.CharField(default=b'#2c689c', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_3_new_win',
            field=models.CharField(default=b'false', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_4_as_button',
            field=models.CharField(default=b'true', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_4_button_colour',
            field=models.CharField(default=b'#000', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_4_button_hover',
            field=models.CharField(default=b'#000000', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_button_4_link_colour',
            field=models.CharField(default=b'#2c689c', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_cookie_bar_as',
            field=models.CharField(default=b'banner', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_data_controller',
            field=models.TextField(default=b'#DATA_CONTROLLER'),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_data_controller_address',
            field=models.TextField(default=b'#DATA_CONTROLLER_ADDRESS'),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_data_controller_email',
            field=models.TextField(default=b'#DATA_CONTROLLER_EMAIL'),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_data_controller_phone',
            field=models.TextField(default=b'#DATA_CONTROLLER_PHONE'),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_font_family',
            field=models.CharField(default=b'inherit', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_header_fix',
            field=models.CharField(default=b'false', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_leave_url',
            field=models.TextField(default=b'#'),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_logging_on',
            field=models.CharField(default=b'false', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_notify_animate_hide',
            field=models.CharField(default=b'true', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_notify_animate_show',
            field=models.CharField(default=b'false', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_notify_div_id',
            field=models.CharField(default=b'#cookie-law-info-bar', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_notify_position_horizontal',
            field=models.CharField(default=b'right', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_notify_position_vertical',
            field=models.CharField(default=b'bottom', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_popup_overlay',
            field=models.CharField(default=b'true', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_popup_showagain_position',
            field=models.CharField(default=b'bottom-right', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_reject_close_reload',
            field=models.CharField(default=b'false', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_scroll_close',
            field=models.CharField(default=b'false', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_scroll_close_reload',
            field=models.CharField(default=b'false', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_show_once',
            field=models.CharField(default=b'10000', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_show_once_yn',
            field=models.CharField(default=b'false', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_showagain_background',
            field=models.CharField(default=b'#fff', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_showagain_border',
            field=models.CharField(default=b'#000', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_showagain_div_id',
            field=models.CharField(default=b'#cookie-law-info-again', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_showagain_head',
            field=models.TextField(default=b'Privacy & Cookies Policy'),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_showagain_tab',
            field=models.CharField(default=b'true', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_showagain_x_position',
            field=models.CharField(default=b'30px', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_text',
            field=models.CharField(default=b'#ffffff', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='cookie_law_info_widget_position',
            field=models.CharField(default=b'left', max_length=30),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='jumbotron_text_color',
            field=models.CharField(default=b'#ffffff', max_length=10),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='jumbotron_title_color',
            field=models.CharField(default=b'#ffffff', max_length=10),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='navbar_dropdown_menu',
            field=models.CharField(default=b'#2c689c', max_length=10),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='navbar_dropdown_menu_divider',
            field=models.CharField(default=b'#204d74', max_length=10),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='navbar_dropdown_menu_hover',
            field=models.CharField(default=b'#204d74', max_length=10),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='navbar_dropdown_menu_text',
            field=models.CharField(default=b'#ffffff', max_length=10),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='navbar_text_color',
            field=models.CharField(default=b'#ffffff', max_length=10),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='navbar_text_hover',
            field=models.CharField(default=b'#2c689c', max_length=10),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='navbar_text_hover_focus',
            field=models.CharField(default=b'#2c689c', max_length=10),
        ),
    ]
