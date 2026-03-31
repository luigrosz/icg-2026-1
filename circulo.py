import math

import glfw
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_LINE_STRIP,
    GL_POLYGON,
    glBegin,
    glClear,
    glClearColor,
    glColor3f,
    glEnd,
    glLineWidth,
    glVertex2f,
)


def main():
    if not glfw.init():
        return

    window = glfw.create_window(800, 800, "Ovo Roxo", None, None)

    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    glClearColor(0.95, 0.95, 0.95, 1.0)

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT)

        glColor3f(0.85, 0.85, 0.85)
        glBegin(GL_POLYGON)
        for i in range(100):
            theta = 2.0 * math.pi * i / 100
            x = 0.05 + 0.55 * math.cos(theta)
            y = -0.05 + 0.7 * math.sin(theta)
            glVertex2f(x, y)
        glEnd()

        glColor3f(0.5, 0.3, 0.8)
        glBegin(GL_POLYGON)
        for i in range(100):
            theta = 2.0 * math.pi * i / 100
            x = 0.55 * math.cos(theta)
            y = 0.7 * math.sin(theta)
            glVertex2f(x, y)
        glEnd()

        glColor3f(0.7, 0.5, 0.9)
        glBegin(GL_POLYGON)
        for i in range(50):
            theta = 2.0 * math.pi * i / 50
            x = -0.22 + 0.16 * math.cos(theta)
            y = 0.28 + 0.18 * math.sin(theta)
            glVertex2f(x, y)
        glEnd()

        glLineWidth(3.0)
        glColor3f(1.0, 1.0, 0.2)
        glBegin(GL_LINE_STRIP)
        for i in range(100):
            x = -0.50 + (1.0 * i / 99.0)
            y = 0.05 + 0.06 * math.sin(x * 15.0)
            glVertex2f(x, y)
        glEnd()

        glColor3f(0.2, 0.7, 1.0)
        glBegin(GL_LINE_STRIP)
        for i in range(100):
            x = -0.50 + (1.0 * i / 99.0)
            y = -0.15 + 0.06 * math.sin(x * 15.0)
            glVertex2f(x, y)
        glEnd()

        glColor3f(1.0, 1.0, 1.0)

        glBegin(GL_POLYGON)
        for i in range(30):
            theta = 2.0 * math.pi * i / 30
            x = -0.25 + 0.07 * math.cos(theta)
            y = -0.4 + 0.05 * math.sin(theta)
            glVertex2f(x, y)
        glEnd()

        glBegin(GL_POLYGON)
        for i in range(30):
            theta = 2.0 * math.pi * i / 30
            x = 0.0 + 0.07 * math.cos(theta)
            y = -0.5 + 0.05 * math.sin(theta)
            glVertex2f(x, y)
        glEnd()

        glBegin(GL_POLYGON)
        for i in range(30):
            theta = 2.0 * math.pi * i / 30
            x = 0.25 + 0.07 * math.cos(theta)
            y = -0.4 + 0.05 * math.sin(theta)
            glVertex2f(x, y)
        glEnd()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


main()
