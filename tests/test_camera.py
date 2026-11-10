from dungeon.camera import Camera


def big_world_camera():
    return Camera(view_w=1000, view_h=600, world_w=3000, world_h=2000)


def test_player_in_the_middle_of_a_big_floor_is_centred():
    camera = big_world_camera()
    camera.snap_to(1500, 1000)
    assert camera.to_screen(1500, 1000) == (500, 300)


def test_camera_stops_at_the_edges_of_the_floor():
    camera = big_world_camera()
    camera.snap_to(0, 0)                      # top-left corner
    assert (camera.x, camera.y) == (0, 0)
    camera.snap_to(3000, 2000)                # bottom-right corner
    assert (camera.x, camera.y) == (2000, 1400)


def test_a_floor_smaller_than_the_view_is_centred():
    camera = Camera(view_w=1000, view_h=600, world_w=400, world_h=200)
    camera.snap_to(10, 10)
    assert camera.to_screen(0, 0) == (300, 200)   # equal empty space on both sides


def test_move_towards_gets_closer_but_does_not_jump():
    camera = big_world_camera()
    camera.snap_to(500, 300)
    camera.move_towards(1500, 1000, dt=1 / 60)
    assert 0 < camera.x < 1000 and 0 < camera.y < 700


def test_move_towards_never_overshoots_on_a_slow_frame():
    camera = big_world_camera()
    camera.snap_to(500, 300)
    camera.move_towards(1500, 1000, dt=5.0)   # a 5 second freeze
    assert (camera.x, camera.y) == (1000, 700)
