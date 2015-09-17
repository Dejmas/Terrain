#version 130

uniform sampler2D  blendTexture; 
uniform sampler2D  text1;
uniform sampler2D  text2;
uniform sampler2D  text3;

varying vec3 N;
varying vec3 v;
varying float fogFactor;
vec4 sature( vec4 c )
{
	float s = 0.30 * c.r + 0.59 * c.g + 0.11 * c.b;
	return vec4( s, s, s, 1 );
}

void main (void)
{
	vec3 L = normalize(gl_LightSource[0].position.xyz - v); 
	vec3 E = normalize(-v); // we are in Eye Coordinates, so EyePos is (0,0,0)
	vec3 R = normalize(-reflect(L,N)); 

	//calculate Ambient Term:
	vec4 amb = gl_FrontLightProduct[0].ambient;

	//calculate Diffuse Term:
	vec4 diff = sature( gl_FrontLightProduct[0].diffuse * clamp(dot(N,L), 0.0, 1.0) );

	// calculate Specular Term:
	vec4 spec = gl_FrontLightProduct[0].specular 
	                  * pow(clamp(dot(R,E),0.0, 1.0),0.3*gl_FrontMaterial.shininess);

	// blend texture
	vec2 btcoord = gl_TexCoord[0].xy;
	vec2 coord = gl_TexCoord[1].xy;
	vec3 bt = texture2D(blendTexture, btcoord).rgb; //original color
	float totalInv = 1./(bt.r + bt.g + bt.b);
	vec3 t1 = texture2D(text1, coord).rgb * bt.g * totalInv;
	vec3 t2 = texture2D(text2, coord).rgb * bt.r * totalInv;
	vec3 t3 = texture2D(text3, coord).rgb * bt.b * totalInv;

	// write Total Color:
	vec3 c = (t1+t2+t3) * (vec3(0.3)+diff.xyz*8.) + spec.xyz; 


	gl_FragColor = mix( gl_Fog.color, vec4( c, 1.0), fogFactor); 

}