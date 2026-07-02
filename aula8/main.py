#!/usr/bin/env python3
"""
Aula 8 — Shaders com iluminação programável (GLSL)

Exercício 1: Efeito de alerta no Fragment Shader.
Uniforme 'uTime' enviado pelo Python. Componente difusa oscila entre
intensidade original e vermelho máximo via sin().

Exercício 2: Controle dinâmico do expoente especular (shininess) via teclado.
Teclas 1-5 alternam entre material fosco (1) e metal polido (128).
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
    glBindAttribLocation(prog, 1, "aNormal")
    glBindAttribLocation(prog, 2, "aColor")
    glLinkProgram(prog)
    if glGetProgramiv(prog, GL_LINK_STATUS) != GL_TRUE:
        print(f"Erro link:\n{glGetProgramInfoLog(prog).decode()}")
        return None
    glDeleteShader(vs); glDeleteShader(fs)
    return prog

# ── vertex data generation ─────────────────────────────────

def make_cube(s=0.5):
    """36 verts: 6 faces x 2 tris x 3 verts.  Layout: pos3 norm3 col3."""
    d = s
    v = [(-d,-d,-d),( d,-d,-d),( d, d,-d),(-d, d,-d),
         (-d,-d, d),( d,-d, d),( d, d, d),(-d, d, d)]
    c = [(0.10,0.30,1.00),(0.10,0.80,1.00),(0.10,1.00,0.50),(0.50,1.00,0.10),
         (0.20,0.10,0.90),(0.80,0.10,0.90),(1.00,1.00,1.00),(0.30,0.30,1.00)]
    faces = [
        (4,5,6,7, 0,0,1),   # frente
        (1,0,3,2, 0,0,-1),  # tras
        (4,5,1,0, 0,-1,0),  # baixo
        (7,6,2,3, 0,1,0),   # cima
        (0,4,7,3, -1,0,0),  # esq
        (1,5,6,2, 1,0,0),   # dir
    ]
    verts = []
    for i0,i1,i2,i3,nx,ny,nz in faces:
        for idx in (i0,i1,i2):
            verts.extend(v[idx]); verts.extend((nx,ny,nz)); verts.extend(c[idx])
        for idx in (i0,i2,i3):
            verts.extend(v[idx]); verts.extend((nx,ny,nz)); verts.extend(c[idx])
    return verts, 36

def make_octahedron(r=0.8):
    """24 verts: 8 faces triangulares.  Layout: pos3 norm3 col3."""
    top,bot = (0,r,0),(0,-r,0)
    rgt,lft = (r,0,0),(-r,0,0)
    frt,bck = (0,0,r),(0,0,-r)
    cols = {top:(1,1,0.1),bot:(1,0.4,0),rgt:(1,0.6,0),lft:(1,0.8,0),
            frt:(1,0.9,0.1),bck:(0.9,0.3,0)}
    faces = [
        (top,rgt,frt),(top,frt,lft),(top,lft,bck),(top,bck,rgt),
        (bot,frt,rgt),(bot,lft,frt),(bot,bck,lft),(bot,rgt,bck),
    ]
    verts = []
    n = 0
    for tri in faces:
        p0,p1,p2 = tri
        v1 = (p1[0]-p0[0],p1[1]-p0[1],p1[2]-p0[2])
        v2 = (p2[0]-p0[0],p2[1]-p0[1],p2[2]-p0[2])
        nx = v1[1]*v2[2]-v1[2]*v2[1]
        ny = v1[2]*v2[0]-v1[0]*v2[2]
        nz = v1[0]*v2[1]-v1[1]*v2[0]
        length = math.hypot(math.hypot(nx,ny),nz)
        if length>0: nx,ny,nz = nx/length,ny/length,nz/length
        for vtx in tri:
            verts.extend(vtx); verts.extend((nx,ny,nz)); verts.extend(cols[vtx])
            n += 1
    return verts, n

# ── VBO helpers ────────────────────────────────────────────

def make_vbo(data):
    arr = (ctypes.c_float*len(data))(*data)
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(arr), arr, GL_STATIC_DRAW)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    return vbo

def draw_vbo(vbo, count, mode=GL_TRIANGLES):
    stride = 9 * ctypes.sizeof(ctypes.c_float)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(0));           glEnableVertexAttribArray(0)
    glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(3*4));          glEnableVertexAttribArray(1)
    glVertexAttribPointer(2,3,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(6*4));          glEnableVertexAttribArray(2)
    glDrawArrays(mode, 0, count)
    glDisableVertexAttribArray(0); glDisableVertexAttribArray(1); glDisableVertexAttribArray(2)
    glBindBuffer(GL_ARRAY_BUFFER, 0)

# ── fixed-function scene elements ──────────────────────────

def draw_stars(count=200, seed=42):
    rng = seed
    def r(): nonlocal rng; rng = (rng*1664525+1013904223)&0xFFFFFFFF; return rng/0xFFFFFFFF
    glPointSize(1.5)
    glColor4f(1,1,1,0.8)
    glBegin(GL_POINTS)
    for _ in range(count):
        th = r()*2*math.pi; ph = math.acos(2*r()-1); R=40
        glVertex3f(R*math.sin(ph)*math.cos(th), R*math.cos(ph), R*math.sin(ph)*math.sin(th))
    glEnd()
    glPointSize(1)

def draw_ring(radius, seg=72):
    glColor4f(0.6,0.6,0.8,0.25)
    glBegin(GL_LINE_LOOP)
    for i in range(seg):
        a=2*math.pi*i/seg; glVertex3f(math.cos(a)*radius,0,math.sin(a)*radius)
    glEnd()

# ── 4x4 matrix helpers (col-major) ─────────────────────────

def identity():
    m=[0.0]*16; m[0]=m[5]=m[10]=m[15]=1.0; return m

def translate(m,x,y,z):
    out=m[:]; out[12]=m[0]*x+m[4]*y+m[8]*z+m[12]
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
    window=glfw.create_window(800,600,"Aula 8 — Shaders com Iluminação",None,None)
    if not window: glfw.terminate(); sys.exit("Falha janela")
    glfw.make_context_current(window); glfw.swap_interval(1)

    glClearColor(0.02,0.02,0.06,1.0)
    glEnable(GL_DEPTH_TEST); glDepthFunc(GL_LEQUAL)
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)

    prog=load_program("aula8/vertex.vs","aula8/fragment.frag")
    if not prog: sys.exit("Falha shaders")
    glUseProgram(prog)

    # uniform locations
    loc_model  = glGetUniformLocation(prog,"model")
    loc_view   = glGetUniformLocation(prog,"view")
    loc_proj   = glGetUniformLocation(prog,"projection")
    loc_lPos   = glGetUniformLocation(prog,"lightPos")
    loc_lCol   = glGetUniformLocation(prog,"lightColor")
    loc_vPos   = glGetUniformLocation(prog,"viewPos")
    loc_time   = glGetUniformLocation(prog,"uTime")      # Exercicio 1
    loc_shiny  = glGetUniformLocation(prog,"uShininess") # Exercicio 2

    # VBOs
    cd,cn=make_cube(0.5); od,on=make_octahedron(0.8)
    cube_vbo=make_vbo(cd); octa_vbo=make_vbo(od)

    # app state
    anim_angle=0.0; anim_speed=1.0
    shininess=32.0   # Exercicio 2: default
    start=glfw.get_time()

    # camera
    cx,cy,cz=0.0,3.0,8.0; cyaw,cpitch=0.0,-18.0
    SPEED=0.08; held=set()

    # light
    lpos=(0.0,4.0,4.0); lcol=(1.0,1.0,0.9)

    def kcb(w,key,_,act,__):
        nonlocal anim_speed,shininess
        if act==glfw.PRESS:
            held.add(key)
            if key==glfw.KEY_ESCAPE: glfw.set_window_should_close(w,True)
            elif key in(glfw.KEY_EQUAL,glfw.KEY_KP_ADD): anim_speed=min(anim_speed*1.5,8)
            elif key in(glfw.KEY_MINUS,glfw.KEY_KP_SUBTRACT): anim_speed=max(anim_speed/1.5,0.1)
            # Exercicio 2: teclas 1-5
            elif key==glfw.KEY_1: shininess=1.0;   print(f"Shininess: {shininess:.0f}  —  Fosco")
            elif key==glfw.KEY_2: shininess=8.0;   print(f"Shininess: {shininess:.0f}  —  Pouco brilho")
            elif key==glfw.KEY_3: shininess=32.0;  print(f"Shininess: {shininess:.0f}  —  Brilho medio")
            elif key==glfw.KEY_4: shininess=64.0;  print(f"Shininess: {shininess:.0f}  —  Brilhante")
            elif key==glfw.KEY_5: shininess=128.0; print(f"Shininess: {shininess:.0f}  —  Metal polido")
        elif act==glfw.RELEASE: held.discard(key)
    glfw.set_key_callback(window,kcb)

    pt=glfw.get_time()
    while not glfw.window_should_close(window):
        now=glfw.get_time(); dt=min(now-pt,0.05); pt=now; elapsed=now-start
        anim_angle+=dt*50.0*anim_speed

        # camera movement
        yr=math.radians(cyaw); fx,fz=-math.sin(yr),-math.cos(yr)
        rx,rz=math.cos(yr),-math.sin(yr)
        if glfw.KEY_W in held: cx+=fx*SPEED; cz+=fz*SPEED
        if glfw.KEY_S in held: cx-=fx*SPEED; cz-=fz*SPEED
        if glfw.KEY_A in held: cx-=rx*SPEED; cz-=rz*SPEED
        if glfw.KEY_D in held: cx+=rx*SPEED; cz+=rz*SPEED
        if glfw.KEY_Q in held: cy+=SPEED
        if glfw.KEY_E in held: cy-=SPEED
        if glfw.KEY_LEFT in held: cyaw-=1.5
        if glfw.KEY_RIGHT in held: cyaw+=1.5
        if glfw.KEY_UP in held: cpitch=min(89.0,cpitch+1.5)
        if glfw.KEY_DOWN in held: cpitch=max(-89.0,cpitch-1.5)

        w,h=glfw.get_framebuffer_size(window)
        glViewport(0,0,w,h)

        # matrices
        proj=perspective(45,w/max(h,1),0.1,100)
        tx=cx-math.sin(math.radians(cyaw))*math.cos(math.radians(cpitch))
        ty=cy+math.sin(math.radians(cpitch))
        tz=cz-math.cos(math.radians(cyaw))*math.cos(math.radians(cpitch))
        view=look_at(cx,cy,cz,tx,ty,tz,0,1,0)

        glClear(int(GL_COLOR_BUFFER_BIT)|int(GL_DEPTH_BUFFER_BIT))

        # ── Fixed-function bg elements ──
        glUseProgram(0)
        draw_stars()
        draw_ring(3.0)
        draw_ring(0.85)

        # ── Objects with lighting ──
        glUseProgram(prog)
        glUniformMatrix4fv(loc_proj,1,GL_FALSE,(ctypes.c_float*16)(*proj))
        glUniformMatrix4fv(loc_view,1,GL_FALSE,(ctypes.c_float*16)(*view))
        glUniform3f(loc_lPos,*lpos); glUniform3f(loc_lCol,*lcol)
        glUniform3f(loc_vPos,cx,cy,cz)

        # Exercicio 1: send time uniform
        glUniform1f(loc_time,elapsed)
        # Exercicio 2: send shininess uniform
        glUniform1f(loc_shiny,shininess)

        # ── SUN (octahedron) ──
        m=identity()
        m=rotate_arb(m,15,1,0,0); m=rotate_y(m,anim_angle*0.6)
        glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))
        draw_vbo(octa_vbo,on)

        # ── PLANET (cube) ──
        pr=math.radians(anim_angle*0.35); px=math.cos(pr)*3; pz=math.sin(pr)*3
        m=identity()
        m=translate(m,px,0,pz)
        m=rotate_arb(m,anim_angle*1.3,0.1,1,0.2); m=scale(m,0.55,0.55,0.55)
        glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))
        draw_vbo(cube_vbo,cn)

        # ── MOON (small octahedron) ──
        mr=math.radians(anim_angle*1.8); mx=math.cos(mr)*0.85; mz=math.sin(mr)*0.85
        m=identity()
        m=translate(m,px,0,pz); m=translate(m,mx,0,mz); m=scale(m,0.25,0.25,0.25)
        m=rotate_arb(m,anim_angle*2.5,1,1,0)
        glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))
        draw_vbo(octa_vbo,on)

        glfw.swap_buffers(window); glfw.poll_events()

    glDeleteProgram(prog); glfw.terminate()

if __name__=="__main__": main()
