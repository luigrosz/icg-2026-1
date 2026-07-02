#!/usr/bin/env python3
"""
Aula 9 — Texturização com OpenGL

Exercício 1: Quadrilátero com textura repetida 3x3.
    Coordenadas UV [0,0] a [3,3] com GL_REPEAT.

Exercício 2: Cubo texturizado com mipmaps.
    glGenerateMipmap, filtro GL_LINEAR_MIPMAP_LINEAR.
    Teclas W/S movem objeto ao longo do eixo Z.
"""

import sys, math, ctypes
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *

# ── shader helpers ──────────────────────────────────────────

def compile_shader(src, stype):
    s = glCreateShader(stype)
    glShaderSource(s, src)
    glCompileShader(s)
    if glGetShaderiv(s, GL_COMPILE_STATUS) != GL_TRUE:
        label = "VERTEX" if stype == GL_VERTEX_SHADER else "FRAGMENT"
        print(f"Erro shader {label}:\n{glGetShaderInfoLog(s).decode()}")
        return None
    return s

def load_program(vs_path, fs_path):
    with open(vs_path) as f: vs_src = f.read()
    with open(fs_path) as f: fs_src = f.read()
    vs = compile_shader(vs_src, GL_VERTEX_SHADER)
    fs = compile_shader(fs_src, GL_FRAGMENT_SHADER)
    if not vs or not fs: return None
    prog = glCreateProgram()
    glAttachShader(prog, vs); glAttachShader(prog, fs)
    glBindAttribLocation(prog, 0, "aPos")
    glBindAttribLocation(prog, 1, "aTexCoord")
    glLinkProgram(prog)
    if glGetProgramiv(prog, GL_LINK_STATUS) != GL_TRUE:
        print(f"Erro link:\n{glGetProgramInfoLog(prog).decode()}")
        return None
    glDeleteShader(vs); glDeleteShader(fs)
    return prog

# ── procedural texture generation ─────────────────────────

def make_checkerboard(w=256, h=256, tiles=4):
    """Gera textura RGBA colorida (tile pattern visível)."""
    pixels = []
    for y in range(h):
        for x in range(w):
            tx = int(x * tiles / w) % 2
            ty = int(y * tiles / h) % 2
            is_white = (tx ^ ty) == 0
            if is_white:
                pixels.extend([255, 200, 100, 255])   # laranja claro
            else:
                pixels.extend([50, 100, 255, 255])    # azul
    return bytes(pixels)

def create_texture(tex_data, width, height, repeat=True, mipmap=False):
    """Cria textura OpenGL com pixels RGBA."""
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)

    # wrapping
    wrap = GL_REPEAT if repeat else GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap)

    # filtros
    if mipmap:
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    else:
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, tex_data)

    if mipmap:
        glGenerateMipmap(GL_TEXTURE_2D)

    glBindTexture(GL_TEXTURE_2D, 0)
    return tex

# ── vertex data generation ─────────────────────────────────

def make_quad_uv3x3():
    """Quad (2 tris) com UV [0,0] a [3,3] para repetição 3x3."""
    verts = [
        # pos x,y,z    u,v
        -1.0, -1.0, 0.0,  0.0, 0.0,
         1.0, -1.0, 0.0,  3.0, 0.0,
         1.0,  1.0, 0.0,  3.0, 3.0,

        -1.0, -1.0, 0.0,  0.0, 0.0,
         1.0,  1.0, 0.0,  3.0, 3.0,
        -1.0,  1.0, 0.0,  0.0, 3.0,
    ]
    return verts, 6  # 6 verts = 2 triangles

def make_cube(s=0.8):
    """36 verts (6 faces x 2 tris x 3 verts). Formato: px,py,pz, u,v.
    UV [0,0] a [1,1] por face."""
    d = s
    v = [(-d,-d,-d),( d,-d,-d),( d, d,-d),(-d, d,-d),
         (-d,-d, d),( d,-d, d),( d, d, d),(-d, d, d)]
    # Cada face: 4 indices + UV corners (u,v) em [0,0]..[1,1]
    faces = [
        (4,5,6,7,  0,0, 1,0, 1,1, 0,1),  # frente
        (1,0,3,2,  0,0, 1,0, 1,1, 0,1),  # tras
        (4,5,1,0,  0,0, 1,0, 1,1, 0,1),  # baixo
        (7,6,2,3,  0,0, 1,0, 1,1, 0,1),  # cima
        (0,4,7,3,  0,0, 1,0, 1,1, 0,1),  # esq
        (1,5,6,2,  0,0, 1,0, 1,1, 0,1),  # dir
    ]
    verts = []
    for i0,i1,i2,i3, u0,v0, u1,v1, u2,v2, u3,v3 in faces:
        # tri1: i0,i1,i2
        for idx,uv in [(i0,(u0,v0)),(i1,(u1,v1)),(i2,(u2,v2))]:
            verts.extend(v[idx]); verts.extend(uv)
        # tri2: i0,i2,i3
        for idx,uv in [(i0,(u0,v0)),(i2,(u2,v2)),(i3,(u3,v3))]:
            verts.extend(v[idx]); verts.extend(uv)
    return verts, 36

# ── VBO helpers ────────────────────────────────────────────

def make_vbo(data):
    arr = (ctypes.c_float*len(data))(*data)
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(arr), arr, GL_STATIC_DRAW)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    return vbo

def draw_vbo(vbo, count, mode=GL_TRIANGLES):
    """Desenha VBO com layout: pos3 + tex2 = 5 floats interleaved."""
    stride = 5 * ctypes.sizeof(ctypes.c_float)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(0));           glEnableVertexAttribArray(0)
    glVertexAttribPointer(1,2,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(3*4));          glEnableVertexAttribArray(1)
    glDrawArrays(mode, 0, count)
    glDisableVertexAttribArray(0); glDisableVertexAttribArray(1)
    glBindBuffer(GL_ARRAY_BUFFER, 0)

# ── matrix helpers (col-major) ─────────────────────────────

def identity():
    m=[0.0]*16; m[0]=m[5]=m[10]=m[15]=1.0; return m

def translate(m,x,y,z):
    out=m[:]
    out[12]=m[0]*x+m[4]*y+m[8]*z+m[12]
    out[13]=m[1]*x+m[5]*y+m[9]*z+m[13]
    out[14]=m[2]*x+m[6]*y+m[10]*z+m[14]
    out[15]=m[3]*x+m[7]*y+m[11]*z+m[15]
    return out

def rotate_y(m,deg):
    rad=math.radians(deg); c=math.cos(rad); s=math.sin(rad); out=m[:]
    out[0]=m[0]*c+m[8]*s;  out[1]=m[1]*c+m[9]*s
    out[2]=m[2]*c+m[10]*s; out[3]=m[3]*c+m[11]*s
    out[8]=-m[0]*s+m[8]*c; out[9]=-m[1]*s+m[9]*c
    out[10]=-m[2]*s+m[10]*c; out[11]=-m[3]*s+m[11]*c
    return out

def rotate_arb(m,deg,ax,ay,az):
    rad=math.radians(deg); c=math.cos(rad); s=math.sin(rad); t=1-c
    L=math.hypot(math.hypot(ax,ay),az)
    if L==0: return m
    x,y,z=ax/L,ay/L,az/L
    rot=[t*x*x+c, t*x*y-z*s, t*x*z+y*s, 0,
         t*x*y+z*s, t*y*y+c, t*y*z-x*s, 0,
         t*x*z-y*s, t*y*z+x*s, t*z*z+c, 0,
         0,0,0,1]
    out=[0.0]*16
    for col in range(4):
        for row in range(4):
            out[col*4+row]=sum(m[col*4+k]*rot[k*4+row] for k in range(4))
    return out

def scale(m,sx,sy,sz):
    out=m[:]; out[0]*=sx; out[1]*=sx; out[2]*=sx; out[3]*=sx
    out[4]*=sy; out[5]*=sy; out[6]*=sy; out[7]*=sy
    out[8]*=sz; out[9]*=sz; out[10]*=sz; out[11]*=sz
    return out

def look_at(ex,ey,ez,cx,cy,cz,ux,uy,uz):
    fl=math.hypot(math.hypot(cx-ex,cy-ey),cz-ez)
    if fl==0: return identity()
    fx,fy,fz=(cx-ex)/fl,(cy-ey)/fl,(cz-ez)/fl
    ul=math.hypot(math.hypot(ux,uy),uz); ux,uy,uz=ux/ul,uy/ul,uz/ul
    sx=fy*uz-fz*uy; sy=fz*ux-fx*uz; sz=fx*uy-fy*ux
    ux=sy*fz-sz*fy; uy=sz*fx-sx*fz; uz=sx*fy-sy*fx
    return [sx,ux,-fx,0, sy,uy,-fy,0, sz,uz,-fz,0,
            -sx*ex-sy*ey-sz*ez, -ux*ex-uy*ey-uz*ez, fx*ex+fy*ey+fz*ez, 1]

def perspective(fov,aspect,near,far):
    f=1.0/math.tan(math.radians(fov)/2); r=1.0/(near-far)
    return [f/aspect,0,0,0, 0,f,0,0, 0,0,(far+near)*r,-1,  0,0,2*far*near*r,0]

# ── main ───────────────────────────────────────────────────

def main():
    if not glfw.init(): sys.exit("Falha GLFW")
    window=glfw.create_window(800,600,"Aula 9 — Texturização",None,None)
    if not window: glfw.terminate(); sys.exit("Falha janela")
    glfw.make_context_current(window); glfw.swap_interval(1)

    glClearColor(0.1,0.1,0.1,1.0)
    glEnable(GL_DEPTH_TEST); glDepthFunc(GL_LEQUAL)

    prog=load_program("aula9/vertex.vs","aula9/fragment.frag")
    if not prog: sys.exit("Falha shaders")
    glUseProgram(prog)

    loc_model = glGetUniformLocation(prog,"model")
    loc_view  = glGetUniformLocation(prog,"view")
    loc_proj  = glGetUniformLocation(prog,"projection")
    loc_tex   = glGetUniformLocation(prog,"uTexture")

    # ── texture (procedural checkerboard) ──
    tex_data = make_checkerboard(256, 256, 4)

    # Ex1: textura com GL_REPEAT para o quad (UV [0,0]-[3,3])
    tex_repeat = create_texture(tex_data, 256, 256, repeat=True, mipmap=False)

    # Ex2: textura com mipmap para o cubo
    tex_mipmap = create_texture(tex_data, 256, 256, repeat=True, mipmap=True)

    # ── VBOs ──
    qd, qn = make_quad_uv3x3()
    cd, cn = make_cube(0.8)
    quad_vbo = make_vbo(qd)
    cube_vbo = make_vbo(cd)

    # ── state ──
    cube_z = -3.0   # Exercício 2: posição Z do cubo (W/S altera)
    angle = 0.0
    held = set()

    def kcb(w,key,_,act,__):
        nonlocal cube_z
        if act==glfw.PRESS:
            held.add(key)
            if key==glfw.KEY_ESCAPE: glfw.set_window_should_close(w,True)
        elif act==glfw.RELEASE:
            held.discard(key)
    glfw.set_key_callback(window,kcb)

    # camera
    view_mat = look_at(0,0,5, 0,0,0, 0,1,0)

    pt=glfw.get_time()
    while not glfw.window_should_close(window):
        now=glfw.get_time(); dt=min(now-pt,0.05); pt=now
        angle += dt * 30.0

        # Exercício 2: W/S move cubo ao longo do eixo Z
        if glfw.KEY_W in held: cube_z -= 0.05  # para perto
        if glfw.KEY_S in held: cube_z += 0.05  # para longe

        w,h=glfw.get_framebuffer_size(window)
        glViewport(0,0,w,h)

        proj = perspective(45, w/max(h,1), 0.1, 100)

        glClear(int(GL_COLOR_BUFFER_BIT)|int(GL_DEPTH_BUFFER_BIT))
        glUseProgram(prog)
        glUniformMatrix4fv(loc_proj,1,GL_FALSE,(ctypes.c_float*16)(*proj))
        glUniformMatrix4fv(loc_view,1,GL_FALSE,(ctypes.c_float*16)(*view_mat))
        glUniform1i(loc_tex, 0)  # texture unit 0

        # ============================================================
        # Exercício 1: Quad com textura repetida 3x3 (UV [0,0]-[3,3])
        # ============================================================
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, tex_repeat)

        m = identity()
        m = translate(m, -2.2, 0, -4)  # posiciona à esquerda
        m = rotate_arb(m, 30, 1, 0, 0)  # inclina pra ficar visível
        glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))
        draw_vbo(quad_vbo, qn)

        # ============================================================
        # Exercício 2: Cubo texturizado com mipmaps
        # ============================================================
        glBindTexture(GL_TEXTURE_2D, tex_mipmap)

        m = identity()
        m = translate(m, 2.2, 0, cube_z)     # posiciona à direita, Z variável
        m = rotate_y(m, angle)                # gira pra mostrar faces
        m = rotate_arb(m, angle * 0.6, 0, 1, 0.3)
        glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))
        draw_vbo(cube_vbo, cn)

        glfw.swap_buffers(window); glfw.poll_events()

    glDeleteProgram(prog); glfw.terminate()

if __name__=="__main__": main()
