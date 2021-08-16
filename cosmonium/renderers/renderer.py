from .pointsrenderer import PointsRenderer
from .resolvedrenderer import ResolvedRenderer
from .labelsrenderer import LabelsRenderer
from .orbitsrenderer import OrbitsRenderer

from .. import settings

class Renderer:
    def __init__(self, context):
        self.objects = []
        self.orbits = []
        self.points_renderer = PointsRenderer(context)
        self.resolved_renderer = ResolvedRenderer(context)
        self.labels_renderer = LabelsRenderer(context)
        self.orbits_renderer = OrbitsRenderer(context)

    def reset(self):
        self.objects = []
        self.orbits = []
        self.points_renderer.reset()
        self.resolved_renderer.reset()
        self.labels_renderer.reset()
        self.orbits_renderer.reset()

    def add_object(self, object_to_render):
        self.objects.append(object_to_render)

    def add_objects(self, objects_to_render):
        self.objects += objects_to_render

    def add_orbit(self, orbit_to_render):
        self.orbits.append(orbit_to_render)

    def add_orbits(self, orbits_to_render):
        self.orbits += orbits_to_render

    def render(self, observer):
        pixel_size = observer.pixel_size
        for orbit_to_render in self.orbits:
            if orbit_to_render.has_orbit and orbit_to_render.anchor.orbit.is_dynamic() and orbit_to_render.anchor.orbit.get_apparent_radius() / (orbit_to_render.anchor.distance_to_obs * pixel_size) > settings.orbit_fade:
                self.orbits_renderer.add_orbit(orbit_to_render)
        for object_to_render in self.objects:
            if object_to_render.anchor.visible:
                self.points_renderer.add_point(object_to_render.anchor.point_color, object_to_render.scene_anchor.scene_position, object_to_render.anchor.visible_size, object_to_render.anchor._app_magnitude, object_to_render.oid_color)
                if object_to_render.has_resolved_halo:
                    self.points_renderer.add_halo(object_to_render.anchor.point_color, object_to_render.scene_anchor.scene_position, object_to_render.anchor.visible_size, object_to_render.anchor._app_magnitude, object_to_render.oid_color)
                if object_to_render.anchor.resolved:
                    self.resolved_renderer.add_body(object_to_render)
            self.labels_renderer.add_label(object_to_render)
        self.points_renderer.render(observer)
        self.resolved_renderer.render(observer)
        self.labels_renderer.render(observer)
        self.orbits_renderer.render(observer)
