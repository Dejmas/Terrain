#version 130
uniform sampler2D  baseTexture; 
uniform sampler2D  bumpTexture;
out vec2 myVerPos;

void main( void )
{
    gl_Position = ftransform();

    myVerPos = gl_Vertex.xy;
}