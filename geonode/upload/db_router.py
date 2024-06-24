#########################################################################
#
# Copyright (C) 2022 OSGeo
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
class DatastoreRouter:
    """
    Router for redirect the resources into the datastore db
    """

    foi_model = {
        "app_label": ["geonode_importer", "dynamic_models"],
    }

    def db_for_read(self, model, **hints):
        """
        Redirect to the datastore model for the FeatureOfInterest
        """
        if model._meta.app_label in self.foi_model.get("app_label"):
            return "datastore"
        return None

    def db_for_write(self, model, **hints):
        """
        Redirect to the datastore model for the FeatureOfInterest
        """
        if model._meta.app_label in self.foi_model.get("app_label"):
            return "datastore"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Redirect to the datastore model for the FeatureOfInterest
        """
        if (
            obj1._meta.app_label in self.foi_model.get("app_label")
            or obj2._meta.app_label == "layer"
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Redirect to the datastore model for the FeatureOfInterest
        """
        if app_label in self.foi_model.get("app_label"):
            return db == "datastore"
        return None if db == "default" else False
