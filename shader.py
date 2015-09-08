from ctypes import *
from pyglet.gl import *

class Shader:
    """docstring for Shader
        code        - string of source code
        shaderType  - GL_VERTEX_SHADER or GL_FRAGMENT_SHADER or GL_GEOMETRY_SHADER
    """
    def __init__(self, vs, fs):
        self.programId = glCreateProgram()

        self.createShader(vs, GL_VERTEX_SHADER)
        self.createShader(fs, GL_FRAGMENT_SHADER)

    def createShader(self, code, shaderType):
        lenght = len(code)
        if not lenght: return

        code = (c_char_p * lenght)(*code)
        self.shaderType = shaderType
        self.shaderId = glCreateShader(shaderType)
        self.programId = glCreateProgram()
        # POINTER(c_char_p)
        glShaderSource(self.shaderId, lenght, cast(pointer(code), POINTER(POINTER(c_char))), None)
        
        glCompileShader(self.shaderId)
        if self.shaderErrorLog(GL_COMPILE_STATUS): return
        glAttachShader(self.programId, self.shaderId)

        glLinkProgram(self.programId)
        if self.programErrorLog(GL_LINK_STATUS): return

        glValidateProgram(self.programId);
        if self.programErrorLog(GL_VALIDATE_STATUS): return



    def shaderErrorLog(self, order):
        ''' return true if is error'''
        res = c_int(0)
    
        glGetShaderiv(self.shaderId, order, byref(res))
        if not res.value :
            glGetShaderiv(self.shaderId, GL_INFO_LOG_LENGTH, byref(res))
            infoLog = create_string_buffer(res.value)
            glGetShaderInfoLog( self.shaderId, res, None, infoLog)

            print "Shader error"
            print infoLog.value
            return True
        return False

    def Use(self):
        glUseProgram(self.programId)

    def Unuse(s=None): glUseProgram(0)

    def programErrorLog(self, order):
        res = c_int(0)
        glGetProgramiv(self.programId, order, byref(res))
        if not res.value :
            glGetProgramiv(self.programId, GL_INFO_LOG_LENGTH, byref(res))
            infoLog = create_string_buffer(res.value)
            glGetProgramInfoLog( self.shaderId, res, None, infoLog)

            print "Program error."
            print infoLog.value
            return True
        return False

    def uniformf(self, name, *vals):
        if len(vals) in range(1, 5):
            varId = glGetUniformLocation(self.programId, name)
            { # switch
                1 : glUniform1f,
                2 : glUniform2f,
                3 : glUniform3f,
                4 : glUniform4f
            }[len(vals)](varId, *vals)

    def uniformi(self, name, *vals):
        if len(vals) in range(1, 5):
            varId = glGetUniformLocation(self.programId, name)
            { # switch
                1 : glUniform1i,
                2 : glUniform2i,
                3 : glUniform3i,
                4 : glUniform4i
            }[len(vals)](varId, *vals)

    def uniform3fv(self, name, *vals):
        varId = glGetUniformLocation(self.programId, name)
        data = (c_float * len(vals))(*vals)
        glUniform3fv(varId, len(vals)/3, data)
        #glUniform3fv = _get_function('glUniform3fv', [_ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float)], None)

    def uniform_mat44f(self, name, *vals):
        varId = glGetUniformLocation(self.programId, name)
        glUniformMatrix4fv(varId, 1, False, (c_float * 16)(* vals))

        # glDettachShader(self.programId, self.shader)
        # glDeleteShader(self.shaderId)

##          TEST          ##


vshader = '''attribute vec2 aVertexPosition;
        void main() {
            gl_Position = vec4(0,0, 0, 1);
        }'''
    
fshader = '''//#extension GL_EXT_GPU_SHADER4 : require
                //#ifdef GL_FRAGMENT_PRECISION_HIGH
                //  precision highp float;
                //#else
                //  precision mediump float;
                //#endif
                //  precision mediump int;
                    const vec2 uCanvasSize = vec2(600,600);
                    uniform vec2 uOffset; //= vec2(-0.5, 0.5);
                    uniform float uScale; //= 1.35;
            
                    vec4 calc(vec2 texCoord) {
                        float x = 0.0;
                        float y = 0.0;
                        float v = 10000.0;
                        float j = 10000.0;
                        const int depth = 500;
                        for (int iteration = 0; iteration < depth; ++iteration) {
                            float xtemp = x*x-y*y+texCoord.x;
                            y = 2.0*x*y+texCoord.y;
                            x = xtemp;
                            v = min(v, abs(x*x+y*y));
                            j = min(j, abs(x*y));
                            if (x*x+y*y >= 4.0) {
            
                                float d = (float(iteration) - (log(log(sqrt(x*x+y*y))) / log(2.0))) / 50.0;
                                v = (1.0 - v) / 2.0;
                                j = (1.0 - j) / 2.0;
                                return vec4(d+j,d,d+v,1);
                            }
                        }
                        return vec4(0,0,0,1);
                    }
            
                    void main() {
                        vec2 texCoord = (gl_FragCoord.xy / uCanvasSize.xy) * 2.0 - vec2(1.0,1.0);
                        texCoord = texCoord * uScale + uOffset;
                        gl_FragColor = calc(texCoord);
                    }'''

testShader = Shader(vs=vshader, fs=fshader)
def quad( x, y, color, size=50 ):
    coords = ( x, y, x + size, y, x + size, y + size, x, y + size );
    colors = color +  color + color + color;
    triglist = [ 0, 1, 2, 2, 3, 0 ];
    vertex_list = pyglet.graphics.vertex_list_indexed( 4,
        triglist,
        ('v2f', coords), 
        ('c3f', colors) );
    return vertex_list

import pyglet
class Win(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(Win, self).__init__(*args, **kwargs)
        testShader.Use()
        self.offset = [-.5, .5]
        self.scale = 1.35
        self.press = [0, 0, 0, 0]
        pyglet.clock.schedule_interval(lambda dt: None, 1.0/60.0)


    def on_resize(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0,1,0,1, -1, 1)
        glMatrixMode(GL_MODELVIEW)


    def on_draw(self):
        o = self.offset
        s = self.scale
        p = self.press
        o[0] = o[0] + p[0]*s*0.01
        o[1] = o[1] + p[1]*s*0.01
        if p[2] < 0: s /= 1.01 
        if p[2] > 0: s *= 1.01

        testShader.uniformf("uScale", s)
        testShader.uniformf("uOffset", *o)
        self.scale = s
        self.clear()
        quad(0, 0, (1, 0, 0), 1).draw(GL_TRIANGLES)


    def on_key_press( self, symbol, modifier ):
        from pyglet.window import key
        if symbol in (key.A, key.LEFT):
            self.press[0] = -1
        elif symbol in (key.W, key.UP):
            self.press[1] = 1
        elif symbol in (key.S, key.DOWN):
            self.press[1] = -1
        elif symbol in (key.D, key.RIGHT):
            self.press[0] = 1

        elif symbol ==  key.O:
            self.press[2] = 1
        elif symbol == key.P:
            self.press[2] = -1

    def on_key_release( self, symbol, modifier ):
        from pyglet.window import key

        if symbol in (key.A, key.LEFT):
            self.press[0] = 0
        elif symbol in (key.W, key.UP):
            self.press[1] = 0
        elif symbol in (key.S, key.DOWN):
            self.press[1] = 0
        elif symbol in (key.D, key.RIGHT):
            self.press[0] = 0

        elif symbol ==  key.O:
            self.press[2] = 0
        elif symbol == key.P:
            self.press[2] = 0



def main():
    w = Win(width=600, height=600, caption='Pyglet', resizable=True)
    pyglet.app.run()


if __name__ == '__main__':
    main()
