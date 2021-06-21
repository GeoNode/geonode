#########################################################################
#
# Copyright (C) 2020 OSGeo
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

# this file will be used to provide custom translation strings from e.g. fixtures
# it will be parsed by python manage.py makemessages and update the .po files accordingly

from django.utils.translation import ugettext as _

texts = [
    _("Flora and/or fauna in natural environment. Examples: wildlife, vegetation, biological sciences, ecology, "
      "wilderness, sealife, wetlands, habitat."),
    _("Biota"),
    _("Legal land descriptions. Examples: political and administrative boundaries."),
    _("Boundaries"),
    _("Processes and phenomena of the atmosphere. Examples: cloud cover, weather, climate, atmospheric conditions, "
      "climate change, precipitation."),
    _("Climatology Meteorology Atmosphere"),
    _("Economic activities, conditions and employment. Examples: production, labour, revenue, commerce, industry, "
      "tourism and ecotourism, forestry, fisheries, commercial or subsistence hunting, exploration and exploitation "
      "of resources such as minerals, oil and gas."),
    _("Economy"),
    _("Height above or below sea level. Examples: altitude, bathymetry, digital elevation models, slope, "
      "derived products."),
    _("Elevation"),
    _("Environmental resources, protection and conservation. Examples: environmental pollution, waste storage and "
      "treatment, environmental impact assessment, monitoring environmental risk, nature reserves, landscape."),
    _("Environment"),
    _("Rearing of animals and/or cultivation of plants. Examples: agriculture, irrigation, aquaculture, "
      "plantations, herding, pests and diseases affecting crops and livestock."),
    _("Farming"),
    _("Information pertaining to earth sciences. Examples: geophysical features and processes, geology, minerals, "
      "sciences dealing with the composition, structure and origin of the earth s rocks, risks of earthquakes, "
      "volcanic activity, landslides, gravity information, soils, permafrost, hydrogeology, erosion."),
    _("Geoscientific Information"),
    _("Health, health services, human ecology, and safety. Examples: disease and illness, factors affecting health, "
      "hygiene, substance abuse, mental and physical health, health services."),
    _("Health"),
    _("Base maps. Examples: land cover, topographic maps, imagery, unclassified images, annotations."),
    _("Imagery Base Maps Earth Cover"),
    _("Inland water features, drainage systems and their characteristics. Examples: rivers and glaciers, salt lakes, "
      "water utilization plans, dams, currents, floods, water quality, hydrographic charts."),
    _("Inland Waters"),
    _("Military bases, structures, activities. Examples: barracks, training grounds, military transportation, "
      "information collection."),
    _("Intelligence Military"),
    _("Positional information and services. Examples: addresses, geodetic networks, control points, postal zones "
      "and services, place names."),
    _("Location"),
    _("Features and characteristics of salt water bodies (excluding inland waters). Examples: tides, tidal waves, "
      "coastal information, reefs."),
    _("Oceans"),
    _("Information used for appropriate actions for future use of the land. Examples: land use maps, zoning maps, "
      "cadastral surveys, land ownership."),
    _("Planning Cadastre"),
    _("Settlements, anthropology, archaeology, education, traditional beliefs, manners and customs, demographic "
      "data, recreational areas and activities, social impact assessments, crime and justice, census information. "
      "Economic activities, conditions and employment."),
    _("Population"),
    _("Characteristics of society and cultures. Examples: settlements, anthropology, archaeology, education, "
      "traditional beliefs, manners and customs, demographic data, recreational areas and activities, social impact "
      "assessments, crime and justice, census information."),
    _("Society"),
    _("Man-made construction. Examples: buildings, museums, churches, factories, housing, monuments, shops, towers."),
    _("Structure"),
    _("Means and aids for conveying persons and/or goods. Examples: roads, airports/airstrips, shipping routes, "
      "tunnels, nautical charts, vehicle or vessel location, aeronautical charts, railways."),
    _("Transportation"),
    _("Energy, water and waste systems and communications infrastructure and services. Examples: hydroelectricity, "
      "geothermal, solar and nuclear sources of energy, water purification and distribution, sewage collection and "
      "disposal, electricity and gas distribution, data communication, telecommunication, radio, communication "
      "networks."),
    _("Utilities Communication")
]
