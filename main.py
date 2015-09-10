#!/usr/bin/python
import pyglet
from pyglet.window import key
from pyglet import image
from pyglet.gl import *
from OpenGL.GLUT import *
from terrain import Terrain
#from sky import SkyBox
from math import *
from shader import Shader, testShader
width = 800
height = 600
glutInit()
WIREFRAME=False
'''
TODOS:
        - blending texture system if possible
        - compile meshes
        - optimaize if is slow
        - more files
        - sky
        - ship
        - car
        - person
        - particle effects

'''

# Define a simple function to create ctypes arrays of floats:
def vec(*args):
        return (GLfloat * len(args))(*args)

def quad( x, y, color, size=50 ):
    coords = ( x, y, x + size, y, x + size, y + size, x, y + size );
    colors = color +  color + color + color;
    triglist = [ 0, 1, 2, 2, 3, 0 ];
    vertex_list = pyglet.graphics.vertex_list_indexed( 4,
        triglist,
        ('v2f', coords), 
        ('c3B', colors) );
    return vertex_list


class Kostka:
    def __init__(self, terrain):
        self.position   = [25, 0, 25]
        self._direction = [ 1, 0, 0 ]
        self.speed      =   0
        self.t          =   terrain
        self.yrot       =   90.
        self.input      = [ False, False ]

    def _calcYrot(self,dt):
        if self.input[0] :
            self.yrot += 100.*dt
        if self.input[1] :
            self.yrot -= 100.*dt

    def calcDirection(self,dt):
        self._calcYrot(dt)
        x = sin(radians(self.yrot))
        z = cos(radians(self.yrot))
        self._direction = x, 0, z

    def update(self, dt):
        self.calcDirection(dt)
        x, y, z = self.position
        dx = self._direction[0] * self.speed * dt
        dz = self._direction[2] * self.speed * dt
        self.position = x+dx, y, z+dz

    def draw(self):
        glDisable(GL_CLIP_PLANE0)
        glColor3f(0,0,1)
        x, y, z = self.position
        y = self.t.Height(x, z, floating=True)
        from math import floor
        xf = int( floor(x) )
        zf = int( floor(z) )
        
        sizes = (GLfloat*10)()
        step = (GLfloat*1)()
        glGetFloatv(GL_POINT_SIZE_RANGE,sizes);
        glGetFloatv(GL_POINT_SIZE_GRANULARITY, step);
        curSize = sizes[0] + 5*step[0]
        glPointSize(curSize);
    
        if xf >= 0 and xf < self.t.a-1 \
        and zf >= 0 and zf < self.t.a-1 :
            glBegin(GL_POINTS)
            # (x, self.hm[z][x], z )
            glVertex3f(xf  , self.t.hm[zf  ][xf  ], zf  )
            glVertex3f(xf+1, self.t.hm[zf  ][xf+1], zf  )
            glVertex3f(xf  , self.t.hm[zf+1][xf  ], zf+1)
            glVertex3f(xf+1, self.t.hm[zf+1][xf+1], zf+1)

            glEnd()

        # cube
        glTranslatef(x, y, z)
        glColor3f(1,0,0)
        glutSolidCube(0.1)
        glTranslatef(-x, -y, -z)


class Window(pyglet.window.Window):


    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        pyglet.clock.schedule_interval(self.update, 1./60)
        self.strafe = [0, 0]

        # Current (x, y, z) position in the world, specified with floats. Note
        # that, perhaps unlike in class, the y-axis is the vertical axis.
        self.position = (12, 8, 12)
        self.press = {}
        self.press["light"] = 0

        # First element is rotation of the player in the x-z plane (ground
        # plane) measured from the z-axis down. The second is the rotation
        # angle from the ground plane up. Rotation is in degrees.
        #
        # The vertical plane rotation ranges from -90 (looking straight down) to
        # 90 (looking straight up). The horizontal rotation range is unbounded.
        self.rotation = (0, 0)
        self.reticle = None
        
        self.t = Terrain(a=33,water_line=1.5,generate=False)
        self.spin = 180
        self.fps = pyglet.clock.ClockDisplay()
        #self.skybox = SkyBox.fromDir("../example/texture/bluesky", "bluesky")
        #self.skybox = SkyBox.fromDir("../example/texture/lake2", "jajlake2")
        self.kostka = Kostka(self.t) 
        self.dlists = {}
        self.dlists['terrain'] = glGenLists(1)
        glNewList(self.dlists['terrain'], GL_COMPILE)
        self.t.draw(5)
        glEndList()
        
        # with open("shader.vs") as vsf:
        #     with  open("shader.fs") as fsf:
        #         self.shader = Shader(vs=vsf.read(), fs=fsf.read())
        #         self.shader.Use()

    def set_exclusive_mouse(self, exclusive):
        """ If `exclusive` is True, the game will capture the mouse, if False
        the game will ignore the mouse.

        """
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive

    def _update(self, dt):
        """ Private implementation of the `update()` method. This is where most
        of the motion logic lives, along with gravity and collision detection.

        Parameters
        ----------
        dt : float
            The change in time since the last call.

        """
        # walking
        speed = 5
        d = dt * speed # distance covered this tick.
        dx, dy, dz = self.get_motion_vector()
        # New position in space, before accounting for gravity.
        dx, dy, dz = dx * d, dy * d, dz * d
        # collisions
        x, y, z = self.position
        self.position = (x + dx, y + dy, z + dz)

        self.kostka.update(dt)

    def update( self, dt ):
        self._update(dt)

    def get_motion_vector(self):
        """ Returns the current motion vector indicating the velocity of the
        player.

        Returns
        -------
        vector : tuple of len 3
            Tuple containing the velocity in x, y, and z respectively.

        """
        if any(self.strafe):
            x, y = self.rotation
            strafe = degrees(atan2(*self.strafe))
            y_angle = radians(y)
            x_angle = radians(x + strafe)
            m = cos(y_angle)
            dy = sin(y_angle)
            if self.strafe[1]:
                # Moving left or right.
                dy = 0.0
                m = 1
            if self.strafe[0] > 0:
                # Moving backwards.
                dy *= -1
            # When you are flying up or down, you have less left and right
            # motion.
            dx = cos(x_angle) * m
            dz = sin(x_angle) * m
            # else:
            #     dy = 0.0
            #     dx = cos(x_angle)
            #     dz = sin(x_angle)
        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0
        return (dx, dy, dz)

    def on_resize(self, width, height):
        """ Called when the window is resized to a new `width` and `height`.

        """
        # label
        #self.label.y = height - 10
        # reticle
        if self.reticle:
            self.reticle.delete()
        x, y = self.width / 2, self.height / 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(4,
            ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n))
        )

    def on_draw(self):
        self.clear()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)  
        self.water_line = 1.5
        self.water_color = (0.3,0.3,1,1)
        
        #self.shader.Use()
        self.set_3d()
        glTranslatef(-16, 0, -16)
        
        # kostka
        #self.shader.uniformf("uScale", 1.35)
        #self.shader.uniformf("uOffset", *[-.5, .5])
        self.kostka.draw()

        #glCallList(self.dlists['terrain'])
        self.t.draw(self.position[1])
        #self.shader.Unuse()

        glPopMatrix() # set_3d camera transf
        self.set_2d()
        glColor3d(0, 0, 0)
        self.fps.draw()

    def set_2d(self):
        """ Configure OpenGL to draw in 2d.

        """
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_3d(self):
        """ Configure OpenGL to draw in 3d.

        """
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 500.0)
        # gluPerspective(65, width / float(height), 15, 0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        # set camera
        glPushMatrix()
        rx, ry = self.rotation
        glRotatef(rx, 0, 1, 0)
        glRotatef(-ry, cos(radians(rx)), 0, sin(radians(rx)))
        x, y, z = self.position
        #y = self.t.Height(x, z, floating=True)+.3
        glTranslatef(-x, -y, -z)
        #self.skybox.draw(yrot=rx, xrot=-ry)


        # set lightning source
        self.spin += 1 #self.press["light"]
        self.spin %= 360
        glPushMatrix();
        x = lambda s : sin(radians(s))*30
        z = lambda s : cos(radians(s))*30
        self.t.lightPos = ( x(self.spin), 15., z(self.spin) )
        #self.shader.uniform3fv("lightPos[0]", *[x(self.spin), 15, z(self.spin)])
        #self.shader.uniform3fv("lightPos[1]", *[x(self.spin+120), 15, z(self.spin+120)])
        #self.shader.uniform3fv("lightPos[2]", *[x(self.spin+240), 15, z(self.spin+240)])
        glTranslatef(0, 30, 0)
        glRotated(self.spin, 0.0, 1.0, 0.0);

        glTranslated (0.0, 0.0, 20.0);
        glLightfv(GL_LIGHT0, GL_POSITION, vec(0, 0, 0, 1))
        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, vec(0, -1, 0))
        glDisable (GL_LIGHTING);
        glColor3f (0.0, 1.0, 1.0);
        glutWireCube (2.0);
        glEnable (GL_LIGHTING);
        glPopMatrix()
   
    def drawChessDesk( self ) :
        glBegin(GL_TRIANGLES)    

        for z in xrange( -30, 30, 1 ) : 
            for x in xrange( -30, 30, 2 ) :
                if z % 2 == 0 :
                    glColor3f(0, 0.5, 0)
                else :
                    glColor3f(.1,.1, .1)

                glNormal3f(0,1,0)
                glVertex3f(x + 1, -5, 1 + z) 
                glVertex3f(x +  0, -5,  0 + z)
                glVertex3f(x +  0, -5, 1 + z) 

                glNormal3f(0,1,0)
                glVertex3f(x +  0, -5,  0 + z)  
                glVertex3f(x + 1, -5, 1 + z)
                glVertex3f(x + 1, -5,  0 + z) 

                if z % 2 != 0:
                    glColor3f(0, 0.5, 0)
                else :
                    glColor3f(.1,.1, .1)

                glNormal3f(0,1,0)
                glVertex3f(x + 2, -5, 1 + z) 
                glVertex3f(x + 1, -5,  0 + z)
                glVertex3f(x + 1, -5, 1 + z) 

                glNormal3f(0,1,0)
                glVertex3f(x + 1, -5,  0 + z)  
                glVertex3f(x + 2, -5, 1 + z)
                glVertex3f(x + 2, -5,  0 + z)    

        glEnd()

    def on_mouse_press(self, x, y, button, modifiers):
        """ Called when a mouse button is pressed. See pyglet docs for button
        amd modifier mappings.

        Parameters
        ----------
        x, y : int
            The coordinates of the mouse click. Always center of the screen if
            the mouse is captured.
        button : int
            Number representing mouse button that was clicked. 1 = left button,
            4 = right button.
        modifiers : int
            Number representing any modifying keys that were pressed when the
            mouse button was clicked.

        """
        if self.exclusive:
            pass
        else:
            self.set_exclusive_mouse(True)

    def on_mouse_motion(self, x, y, dx, dy):
        """ Called when the player moves the mouse.

        Parameters
        ----------
        x, y : int
            The coordinates of the mouse click. Always center of the screen if
            the mouse is captured.
        dx, dy : float
            The movement of the mouse.

        """
        if self.exclusive:
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)

    def on_key_press( self, symbol, modifier ):
        global piece, bottom

        if symbol == key.A:
            self.strafe[1] -= 1
        elif symbol == key.W:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.D:
            self.strafe[1] += 1

        elif symbol == key.UP :
            self.kostka.speed += .1
        elif symbol == key.DOWN :
            self.kostka.speed -= .1 
        elif symbol == key.LEFT :
            self.kostka.input[0] = True
        elif symbol == key.RIGHT :
            self.kostka.input[1] = True

        elif symbol == key.F :
            global WIREFRAME
            WIREFRAME = not WIREFRAME
            if WIREFRAME :
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            else :
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        elif symbol == key.N :
            self.t = Terrain(water_line=1.5,generate=True)
        elif symbol == key.Q :
            exit(0)
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)

        elif symbol == key.O :
            self.press["light"] = 1
        elif symbol == key.P :
            self.press["light"] = -1


    def on_key_release(self, symbol, modifiers):
        """ Called when the player releases a key. See pyglet docs for key
        mappings.

        Parameters
        ----------
        symbol : int
            Number representing the key that was pressed.
        modifiers : int
            Number representing any modifying keys that were pressed.

        """
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1

        elif symbol == key.LEFT :
            self.kostka.input[0] = False
        elif symbol == key.RIGHT :
            self.kostka.input[1] = False

        elif symbol == key.O :
            self.press["light"] = 0
        elif symbol == key.P :
            self.press["light"] = 0


def setup():
    """ Basic OpenGL configuration.

    """
    # Set the color of "clear", i.e. the sky, in rgba.
    glClearColor(0.5, 0.69, 1.0, 1)
    glClearColor(0.26, 0.32, .6, 1)
    # Enable culling (not rendering) of back-facing facets -- facets that aren't
    # visible to you.
    glEnable(GL_CULL_FACE)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    #glEnable(GL_LIGHT1)

    #glLightfv(GL_LIGHT0, GL_POSITION, vec(0, 0, 0, 0))
    #glLightfv(GL_LIGHT0, GL_SPECULAR, vec(1, 1, 1, 0))
    #glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(1, 1, 1, 0))
    pos0 = vec(0.0,0.0,0.0,1.0)
    diffuse0 = vec(.25,.25,.25,.33)
    ambient0 = vec(.33,.33,.33,.33)
    specular0 = vec(.33,.33,.33,.33)
    glLightf(GL_LIGHT0, GL_SPOT_CUTOFF, 75)
    glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.00300);
    glLightfv(GL_LIGHT0, GL_POSITION, pos0)

    glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse0)
    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient0)
    glLightfv(GL_LIGHT0, GL_SPECULAR, specular0)

    glEnable(GL_COLOR_MATERIAL);
    glEnable(GL_NORMALIZE)

def main():
    window = Window(width=width, height=height, caption='Pyglet', resizable=True)
    platform = pyglet.window.get_platform()
    display = platform.get_default_display()

    locx = (display.get_screens()[0].width-width)/2
    locy = (display.get_screens()[0].height-height)/2
    window.set_location( locx, locy )

    # Hide the mouse cursor and prevent the mouse from leaving the window.
    window.set_exclusive_mouse(True)
    setup()
    pyglet.app.run()

if __name__ == '__main__':
    main()
