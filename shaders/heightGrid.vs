#version 130

varying vec3 N;
varying vec3 v;
varying float fogFactor;

void main(void)
{
	// eye zero
	v = vec3(gl_ModelViewMatrix * gl_Vertex);
	// Normala
	N = normalize(gl_NormalMatrix * gl_Normal);
	// vertex MVP transform
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;

	// carrying texture coords to fs
	gl_TexCoord[0] = gl_MultiTexCoord0;
	gl_TexCoord[1] = gl_MultiTexCoord1;

	// set clipping distance
	gl_ClipDistance[0] = dot(gl_ModelViewMatrix * gl_Vertex, gl_ClipPlane[0]);

	// calculate fog coordinate: distance from eye
    gl_FogFragCoord = length(v);
    float d = gl_Fog.density;
    fogFactor = exp(-d*d*gl_FogFragCoord*gl_FogFragCoord);
    fogFactor = clamp(fogFactor, 0.0, 1.0);
}