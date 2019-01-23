import json
from django.test import TestCase, Client


class MapNotesTest(TestCase):
    fixtures = ['mapnotes_data.json']

    def test_get_notes_map(self):
        c = Client()
        response = c.get("/annotations/1?bbox=-180.0,-90.0,180.0,90.0")
        note_json = json.loads(response.content)
        self.assertEquals(2, len(note_json["features"]))
        for feature in note_json["features"]:
            self.assertTrue(feature["id"] == 1 or feature["id"] == 2)

        response = c.get("/annotations/2?bbox=-180.0,-90.0,180.0,90.0")
        note_json = json.loads(response.content)
        self.assertEquals(1, len(note_json["features"]))
        for feature in note_json["features"]:
            self.assertTrue(feature["id"] == 3)

    def test_get_notes_bbox(self):
        c = Client()
        response = c.get("/annotations/1?bbox=-180.0,-90.0,-150.0,-60.0")
        note_json = json.loads(response.content)
        self.assertEquals(0, len(note_json["features"]))

        response = c.get("/annotations/1?bbox=-180.0,-90.0,0.0,0.0")
        note_json = json.loads(response.content)
        self.assertEquals(1, len(note_json["features"]))

    def test_get_specific_note(self):
        c = Client()
        response = c.get("/annotations/1/2")
        note_json = json.loads(response.content)
        self.assertEquals(1, len(note_json["features"]))
        self.assertEquals(2, note_json["features"][0]["id"])
        self.assertEquals("Map Note 2", note_json["features"][0]["properties"]["title"])

    def test_create_new_note(self):
        json_payload = """
            {"type":"FeatureCollection",
            "features":[
                {"type":"Feature","properties":{
                    "title":"A new note",
                    "content":"This is my new note"},
                    "geometry":{"type":"Point","coordinates":[0.08789062499998361,17.81145608856474]}
                }
            ]}
            """
        c = Client()
        c.login(username='bobby', password='bob')
        response = c.post("/annotations/1", data=json_payload, content_type="application/json")
        note_json = json.loads(response.content)
        self.assertEquals(1, len(note_json["features"]))
        self.assertEquals(4, note_json["features"][0]["id"])
        self.assertEquals([0.08789062499998361, 17.81145608856474], note_json["features"][0]["geometry"]["coordinates"])
        self.assertEquals("This is my new note", note_json["features"][0]["properties"]["content"])

    def test_modify_existing_note(self):
        json_payload = """
            {"type":"FeatureCollection",
            "features":[
                {"type":"Feature","properties":{
                    "title":"A modified note",
                    "content":"This is my new note, modified"},
                    "geometry":{"type":"Point","coordinates":[0.38789062499998361,23.81145608856474]}
                }
            ]}
            """
        c = Client()
        c.login(username='bobby', password='bob')
        response = c.post("/annotations/1/1", data=json_payload, content_type="application/json")
        note_json = json.loads(response.content)
        self.assertEquals(1, len(note_json["features"]))
        self.assertEquals(1, note_json["features"][0]["id"])
        self.assertEquals([0.38789062499998361, 23.81145608856474], note_json["features"][0]["geometry"]["coordinates"])
        self.assertEquals("This is my new note, modified", note_json["features"][0]["properties"]["content"])
        self.assertEquals("A modified note", note_json["features"][0]["properties"]["title"])

    def test_note_security(self):
        json_payload = """
            {"type":"FeatureCollection",
            "features":[
                {"type":"Feature","properties":{
                    "title":"Dont modify me",
                    "content":"This note should not be edited"},
                    "geometry":{"type":"Point","coordinates":[40.38789062499998361,43.81145608856474]}
                }
            ]}
            """
        c = Client()
        c.login(username='bobby', password='bob')
        response = c.post("/annotations/1/2", data=json_payload, content_type="application/json")
        self.assertEquals(403, response.status_code)
