import L from "leaflet";
import PubSub from "pubsub-js";

function getBounds() {
  const maxExtent = [89.99, 180];
  const southWest = L.latLng(maxExtent[0] * -1, maxExtent[1] * -1),
    northEast = L.latLng(maxExtent[0], maxExtent[1]);
  return L.latLngBounds(southWest, northEast);
}

export default function({ id = "filter-map" } = {}) {
  if (!$(".leaflet_map").length) {
    return;
  }

  const bounds = getBounds();

  const layers = [
    L.tileLayer("//{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      name: "OpenStreetMap Mapnik",
      continuousWorld: false,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    })
  ];

  const map = L.map(id, {
    center: bounds.getCenter(),
    zoom: 0,
    maxBounds: bounds,
    maxBoundsViscosity: 1.0,
    layers
  });

  map.on("moveend", () => {
    const extent = map.getBounds().toBBoxString();
    map.invalidateSize();
    PubSub.publish("mapMove", extent);
  });

  PubSub.subscribe("sidebarToggle", () => {
    setTimeout(() => {
      map.invalidateSize();
    });
  });

  let showMap = false;
  $("#_extent_filter").click(evt => {
    showMap = !showMap;
    if (showMap) {
      map.invalidateSize();
    }
  });
}
