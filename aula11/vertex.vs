#version 120

attribute vec3 aPos;
attribute vec3 aColor;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

varying vec3 VertColor;

void main()
{
    VertColor = aColor;
    gl_Position = projection * view * model * vec4(aPos, 1.0);
}
