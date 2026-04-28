import glfw
from OpenGL.GL import *
from OpenGL.GLU import *

eye_x, eye_y, eye_z       = 0.0, 3.0, 8.0
center_x, center_y, center_z = 0.0, 0.0, 0.0
up_x, up_y, up_z          = 0.0, 1.0, 0.0


def init():
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glEnable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)


def resize(window, w, h):
    if h == 0:
        h = 1
    glViewport(0, 0, w, h)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, w / h, 0.1, 200.0)

    glMatrixMode(GL_MODELVIEW)


def camera():
    gluLookAt(
        eye_x,    eye_y,    eye_z,
        center_x, center_y, center_z,
        up_x,     up_y,     up_z
    )


def draw_axes():
    glBegin(GL_LINES)

    glColor3f(1, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(10, 0, 0)

    glColor3f(0, 1, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 10, 0)

    glColor3f(0, 0, 1)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, 10)

    glEnd()


def draw_grid():
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINES)
    for i in range(-10, 11):
        glVertex3f(i, 0, -10)
        glVertex3f(i, 0,  10)
        glVertex3f(-10, 0, i)
        glVertex3f( 10, 0, i)
    glEnd()


def draw_cube():
    vertices = [
        [-1, -1, -1], [ 1, -1, -1], [ 1,  1, -1], [-1,  1, -1],
        [-1, -1,  1], [ 1, -1,  1], [ 1,  1,  1], [-1,  1,  1],
    ]
    faces = [
        (0, 1, 2, 3), (4, 5, 6, 7),
        (0, 1, 5, 4), (2, 3, 7, 6),
        (0, 3, 7, 4), (1, 2, 6, 5),
    ]
    colors = [
        (1.0, 0.2, 0.2), (0.2, 1.0, 0.2),
        (0.2, 0.2, 1.0), (1.0, 1.0, 0.2),
        (1.0, 0.5, 0.0), (0.5, 0.0, 1.0),
    ]

    glBegin(GL_QUADS)
    for face, color in zip(faces, colors):
        glColor3f(*color)
        for idx in face:
            glVertex3fv(vertices[idx])
    glEnd()


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    camera()

    draw_grid()
    draw_axes()

    glPushMatrix()
    glTranslatef(0, 1, 0)
    draw_cube()
    glPopMatrix()


def key_callback(window, key, scancode, action, mods):
    global eye_x, eye_y, eye_z
    global center_x, center_y, center_z
    global up_x, up_y, up_z

    step = 0.3
    pan  = 0.2

    if action == glfw.PRESS or action == glfw.REPEAT:
        # --- mover eye (frente/tras/esq/dir/cima/baixo) ---
        if key == glfw.KEY_W:
            eye_z    -= step
            center_z -= step
        elif key == glfw.KEY_S:
            eye_z    += step
            center_z += step

        elif key == glfw.KEY_A:
            eye_x    -= step
            center_x -= step
        elif key == glfw.KEY_D:
            eye_x    += step
            center_x += step

        elif key == glfw.KEY_Q:
            eye_y    += step
            center_y += step
        elif key == glfw.KEY_E:
            eye_y    -= step
            center_y -= step

        # --- mover center (pan da câmera) ---
        elif key == glfw.KEY_UP:
            center_y += pan
        elif key == glfw.KEY_DOWN:
            center_y -= pan
        elif key == glfw.KEY_LEFT:
            center_x -= pan
        elif key == glfw.KEY_RIGHT:
            center_x += pan

        # --- rotacionar vetor up ---
        elif key == glfw.KEY_U:
            up_z -= 0.1
        elif key == glfw.KEY_J:
            up_z += 0.1


def main():
    if not glfw.init():
        return

    window = glfw.create_window(1280, 720, "Aula 5 - Camera", None, None)
    glfw.make_context_current(window)

    glfw.set_window_size_callback(window, resize)
    glfw.set_key_callback(window, key_callback)

    init()

    while not glfw.window_should_close(window):
        display()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
