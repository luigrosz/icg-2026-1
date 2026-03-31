import glfw
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_QUADS,
    glBegin,
    glClear,
    glClearColor,
    glColor3f,
    glEnd,
    glVertex2f,
)


def main():
    if not glfw.init():
        return

    window = glfw.create_window(800, 600, "Chocolate", None, None)

    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    glClearColor(0.0, 0.0, 0.0, 1.0)

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT)

        for linha in range(4):
            for coluna in range(2):
                cx = -0.2 + (coluna * 0.4)
                cy = -0.6 + (linha * 0.4)

                glColor3f(0.25, 0.13, 0.08)
                glBegin(GL_QUADS)
                glVertex2f(cx - 0.2, cy - 0.2)
                glVertex2f(cx + 0.2, cy - 0.2)
                glVertex2f(cx + 0.2, cy + 0.2)
                glVertex2f(cx - 0.2, cy + 0.2)
                glEnd()

                glColor3f(0.40, 0.21, 0.13)
                glBegin(GL_QUADS)
                glVertex2f(cx - 0.14, cy - 0.14)
                glVertex2f(cx + 0.14, cy - 0.14)
                glVertex2f(cx + 0.14, cy + 0.14)
                glVertex2f(cx - 0.14, cy + 0.14)
                glEnd()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


main()
