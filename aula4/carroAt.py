import glfw
import pywavefront
from OpenGL.GL import *
from OpenGL.GLU import *

T = 0
T2 = 0
T3 = -20


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
    gluPerspective(45.0, w / h, 0.1, 100.0)

    glMatrixMode(GL_MODELVIEW)


def load_obj(path):
    vertices = []
    faces = []

    with open(path, "r") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.strip().split()
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])

            elif line.startswith("f "):
                parts = line.strip().split()[1:]
                face = []
                for p in parts:
                    idx = p.split("/")[0]
                    face.append(int(idx) - 1)
                faces.append(face)

    return vertices, faces


def draw_obj(vertices, faces, main_color):
    glBegin(GL_TRIANGLES)
    for i, face in enumerate(faces):
        if i % 2 == 0:
            glColor3f(main_color[0], main_color[1], main_color[2])
        else:
            glColor3f(main_color[0] * 0.6, main_color[1] * 0.6, main_color[2] * 0.6)

        for idx in face:
            glVertex3f(*vertices[idx])
    glEnd()


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


def display(carro_v, carro_f, roda_v, roda_f):
    global T, T2, T3

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    gluLookAt(12, 8, 18, 0, 0, 0, 0, 1, 0)

    glScalef(0.5, 0.5, 0.5)

    glPushMatrix()

    glTranslatef(0, 0, T3)
    glRotatef(T, 0, 1, 0)

    glPushMatrix()
    glTranslatef(0, 1, 0)
    draw_obj(carro_v, carro_f, (1.0, 0.9, 0.0))
    glPopMatrix()

    wheel_color = (0.3, 0.3, 0.3)
    posicoes = [(1.5, 0.5, 2.5), (-1.5, 0.5, 2.5), (1.5, 0.5, -2.5), (-1.5, 0.5, -2.5)]

    for x, y, z in posicoes:
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(T2, 1, 0, 0)
        draw_obj(roda_v, roda_f, wheel_color)
        glPopMatrix()

    glPopMatrix()

    draw_axes()


def key_callback(window, key, scancode, action, mods):
    global T, T2, T3

    move_speed = 0.5
    wheel_spin_speed = 10.0

    if action == glfw.PRESS or action == glfw.REPEAT:
        if key == glfw.KEY_LEFT:
            T += 2
        elif key == glfw.KEY_RIGHT:
            T -= 2

        elif key == glfw.KEY_UP:
            T3 += move_speed
            T2 -= wheel_spin_speed
        elif key == glfw.KEY_DOWN:
            T3 -= move_speed
            T2 += wheel_spin_speed


def main():
    if not glfw.init():
        return

    window = glfw.create_window(1280, 720, "Carro 3D", None, None)
    glfw.make_context_current(window)

    glfw.set_window_size_callback(window, resize)
    glfw.set_key_callback(window, key_callback)

    init()

    carro_v, carro_f = load_obj("RubberDuck.obj")
    roda_v, roda_f = load_obj("roda2.obj")
    while not glfw.window_should_close(window):
        display(carro_v, carro_f, roda_v, roda_f)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
