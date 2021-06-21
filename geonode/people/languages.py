#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

# List of language code and languages local names.
#
# This list is output of code:
# [
#     (code, get_language_info(code).get("name_local"))
#     for code, lang in settings.LANGUAGES
# ]
#

LANGUAGES = [
    ("af", "Afrikaans"),
    ("ar", "العربيّة"),
    ("ast", "asturian"),
    ("az", "Azərbaycanca"),
    ("bg", "български"),
    ("be", "беларуская"),
    ("bn", "বাংলা"),
    ("br", "brezhoneg"),
    ("bs", "bosanski"),
    ("ca", "català"),
    ("cs", "česky"),
    ("cy", "Cymraeg"),
    ("da", "dansk"),
    ("de", "Deutsch"),
    ("el", "Ελληνικά"),
    ("en", "English"),
    ("en-au", "Australian English"),
    ("en-gb", "British English"),
    ("eo", "Esperanto"),
    ("es", "español"),
    ("es-ar", "español de Argentina"),
    ("es-mx", "español de Mexico"),
    ("es-ni", "español de Nicaragua"),
    ("es-ve", "español de Venezuela"),
    ("et", "eesti"),
    ("eu", "Basque"),
    ("fa", "فارسی"),
    ("fi", "suomi"),
    ("fr", "français"),
    ("fy", "frysk"),
    ("ga", "Gaeilge"),
    ("gl", "galego"),
    ("he", "עברית"),
    ("hi", "Hindi"),
    ("hr", "Hrvatski"),
    ("hu", "Magyar"),
    ("ia", "Interlingua"),
    ("id", "Bahasa Indonesia"),
    ("io", "ido"),
    ("is", "Íslenska"),
    ("it", "italiano"),
    ("ja", "日本語"),
    ("ka", "ქართული"),
    ("kk", "Қазақ"),
    ("km", "Khmer"),
    ("kn", "Kannada"),
    ("ko", "한국어"),
    ("lb", "Lëtzebuergesch"),
    ("lt", "Lietuviškai"),
    ("lv", "latvieš"),
    ("mk", "Македонски"),
    ("ml", "Malayalam"),
    ("mn", "Mongolian"),
    ("mr", "मराठी"),
    ("my", "မြန်မာဘာသာ"),
    ("nb", "norsk (bokmål)"),
    ("ne", "नेपाली"),
    ("nl", "Nederlands"),
    ("nn", "norsk (nynorsk)"),
    ("os", "Ирон"),
    ("pa", "Punjabi"),
    ("pl", "polski"),
    ("pt", "Português"),
    ("pt-br", "Português Brasileiro"),
    ("ro", "Română"),
    ("ru", "Русский"),
    ("sk", "slovenský"),
    ("sl", "Slovenščina"),
    ("sq", "shqip"),
    ("sr", "српски"),
    ("sr-latn", "srpski (latinica)"),
    ("sv", "svenska"),
    ("sw", "Kiswahili"),
    ("ta", "தமிழ்"),
    ("te", "తెలుగు"),
    ("th", "ภาษาไทย"),
    ("tr", "Türkçe"),
    ("tt", "Татарча"),
    ("udm", "Удмурт"),
    ("uk", "Українська"),
    ("ur", "اردو"),
    ("vi", "Tiếng Việt"),
    ("zh-cn", "简体中文"),
    ("zh-hans", "简体中文"),
    ("zh-hant", "繁體中文"),
    ("zh-tw", "繁體中文")
]
