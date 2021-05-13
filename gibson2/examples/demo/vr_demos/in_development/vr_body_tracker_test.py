"""
Demo for testing VR body based on torso tracker
"""
from gibson2.robots.behavior_robot import BehaviorRobot
from gibson2.render.mesh_renderer.mesh_renderer_cpu import MeshRendererSettings
from gibson2.scenes.empty_scene import EmptyScene
from gibson2.simulator import Simulator


def main():
    s = Simulator(mode='vr', 
                rendering_settings=MeshRendererSettings(enable_shadow=True, optimized=True))
    scene = EmptyScene()
    s.import_scene(scene, render_floor_plane=True)
    vr_agent = BehaviorRobot(s)

    # Main simulation loop
    while True:
        s.step()
        vr_agent.update()
                

if __name__ == '__main__':
    main()