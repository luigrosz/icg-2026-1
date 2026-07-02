#version 120

varying vec3 VertColor;

void main()
{
    gl_FragColor = vec4(VertColor, 1.0);
}
