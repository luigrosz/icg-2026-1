import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import pywavefront
import sys

# Lembrando que o arquivo obj têm que tá na pasta
try:
    scene = pywavefront.Wavefront('soccer.obj', collect_faces=True, create_materials=True)
except Exception as e:
    print(f"deu erro no arquivo: {e}")
    sys.exit()

def init():
    glClearColor(1.0, 0.4, 0.4, 1.0);
    
    # glEnable(GL_DEPTH_TEST) # Ativando a profundidade para dar a impressão 3D
    # glEnable(GL_LIGHTING)   # Habilitando a luz - Iluminação
    # glEnable(GL_LIGHT0)     
    
    # Jogando luz no dado
    # glLightfv(GL_LIGHT0, GL_POSITION, (10, 10, 10, 1))

def draw_scene(window):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Câmera mais distante pra ver melhor
    gluLookAt(8, 8, 8, 0, 0, 0, 0, 1, 0)
    
    # centralizado o dado pra ver 
    glScalef(0.3, 0.3, 0.3)          
    glTranslatef(0.0, -1.0, 0.0)     
    
    # Rodando o dado pra bater a luz 
    glRotatef(glfw.get_time() * 30, 0, 1, 0)
   
    #desenhando os triângulos do objeto 
    for name, mesh in scene.meshes.items():
        glBegin(GL_TRIANGLES)
        for face in mesh.faces:
            for vertex_i in face:
                glVertex3fv(scene.vertices[vertex_i])
        glEnd()

def main():
    # Inicializando o GLFW... se não der certo retorna erro
    if not glfw.init():
        return

    window = glfw.create_window(800, 600, "Meu dado bunitinho", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    # Configurando a lente da nossa câmera (o FOV)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, 800/600, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

    init()

    # Enquanto não fechar a janela, continua rodado
    while not glfw.window_should_close(window):
        draw_scene(window)
        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate() # Finalizando o programa

if __name__ == "__main__":
    main()