#version 130
uniform sampler2D  blendTexture; 
uniform sampler2D  text1;
uniform sampler2D  text2;
uniform sampler2D  text3;

void main() 
{
	vec2 btcoord = gl_TexCoord[0].xy;
	vec2 coord = gl_TexCoord[1].xy;
	vec3 bt = texture2D(blendTexture, btcoord).rgb; //original color
	vec3 t1 = texture2D(text1, coord).rgb * bt.g;
	vec3 t2 = texture2D(text2, coord).rgb * bt.r;
	vec3 t3 = texture2D(text3, coord).rgb * bt.b;
	
	float r, g, b;
	r = t1.r + t2.r + t3.r;
	g = t1.g + t2.g + t3.g;
	b = t1.b + t2.b + t3.b;

	gl_FragColor = vec4(r, g, b, 1);
}