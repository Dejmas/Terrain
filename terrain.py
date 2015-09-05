#!/usr/bin/python
import pyglet
from pyglet.window import key
from pyglet import image
from pyglet.gl import *
from OpenGL.GLUT import *
import math
from math import sqrt
import pdb

width = 800
height = 600
glutInit()
WIREFRAME=False
'''
TODOS:
        - heights getter for floating objects, and non-floating
        - compile meshes
        - blending texture system if possible
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

class Terrain(object) :
    '''
            Set up sizes a and b same number. Some 2^k + 1, like 17, 33, ... 
            generate - set true if you want new terrain or false to load last.
    '''
    def __init__(self, a=33, b=33, generate=True) :
        self.a = a
        if generate :
            self.generateHeightMap(a, b)
            self.saveHeightMap('hm_last')
        else:
            self.loadHeighMap('hm_last')
        self.loadTexture()
        self.generateGrid(a-1,b-1)

    def generateHeightMap( self, x, y ) :
        '''
            x, y : integers sizes of heightmap 
        '''
        hm = []
        for i in range(y) : hm . append([4]*x)
        hm[0][0] = 2.4
        hm[y-1][0] = 2.1
        hm[0][x-1] = .5
        hm[y-1][x-1] = 3.
        self.hm = hm      
        self.recursion( 0, 0, x-1, y-1 )
        for i in xrange(1,4):
            self.smoothing(x, y, 0.75)

    def saveHeightMap( self, filename):
        from pyglet.image import SolidColorImagePattern
        c = 65, 65, 65, 65
        img = SolidColorImagePattern(c).create_image(self.a, self.a)
        img = img.get_image_data()
        hm = self.hm
        mi = min([i for r in hm for i in r])
        ma = max([i for r in hm for i in r])
        print mi,ma
        height = ma - mi
        toSave = lambda x : int(  (x-mi)*255/height  )
        data2 = ""
        for i in range(self.a):
            for j in range(self.a):
                h = toSave( hm[i][j] )
                r, g, b, a = h, h, h, 255
                data2 += chr(r) + chr(g) + chr(b) + chr(a)
        img.set_data('RGBA', img.width*4, data2)
        img.save('saved/{}.png'.format(filename))
        with open('saved/{}.info'.format(filename), 'w') as file:
            file.write('mi={},ma={}'.format(mi, ma))

    def loadHeighMap( self, filename ):
        hm = []
        mi = ma = height = None
        # load info
        with open('saved/{}.info'.format(filename), 'r') as file:
            line = file.readlines()[0]
            import re
            res = re.match(r'mi=([^,]*),ma=(.*)', line)
            mi = float( res.group(1) )
            ma = float( res.group(2) )
            height = ma - mi
        
        # load image
        img = pyglet.image.load('saved/{}.png'.format(filename))
        img = img.get_image_data()
        data = img.get_data('RGBA', img.width*4)
        a = self.a = img.width
        # create 2d array
        for i in range(a) : hm . append([4]*a)
        
        # load heights
        toLoad = lambda x : ord(x)/255.*height+mi
        # extremizace
        # ex = 1.6 # set 1 to normal        
        # toLoad = lambda x : (ord(x)/255.*height+mi - height/2)*ex +height/2
        for i in xrange(0, img.width*img.height*4, img.width*4):
            for j in xrange(0, img.width*4, 4):
                h = data[i+j] 
                hm[ i /img.width/4][j/4] = toLoad( h )

        self.hm = hm

    def saveNormalMap( self, normals, filename ):
        siz = self.a-1
        from pyglet.image import SolidColorImagePattern
        c = 65, 65, 65, 65
        img = SolidColorImagePattern(c).create_image(siz, siz)
        img = img.get_image_data()
        
        toSave = lambda x : int(  (x+1)*127  )
        data2 = ""
  
        for i in xrange(0, siz**2*3, siz*3):
            for j in range(0, siz*3, 3):
                r, g, b = normals[i+j:i+j+3]
                r, g, b, a = toSave(r), toSave(g), toSave(b), 255
                data2 += chr(r) + chr(g) + chr(b) + chr(a)
        
        img.set_data('RGBA', img.width*4, data2)
        img.save('saved/{}.png'.format(filename))

    def smoothing( self, xs, ys, k = 0.90 ):
        #print "ys, xs = ", ys, xs
        for y in xrange(1,ys):
            for x in xrange(0,xs):
                self.hm[y][x] = self.hm[y-1][x] * (1-k) + self.hm[y][x] * k

        for y in reversed( xrange(0,ys-1) ):
            for x in xrange(0,xs):
                self.hm[y][x] = self.hm[y+1][x] * (1-k) + self.hm[y][x] * k

        for y in xrange(0,ys):
            for x in xrange(1,xs):
                self.hm[y][x] = self.hm[y][x-1] * (1-k) + self.hm[y][x] * k

        for y in xrange(0,ys):
            for x in reversed(xrange(0,xs-1)):
                self.hm[y][x] = self.hm[y][x+1] * (1-k) + self.hm[y][x] * k
              
    def recursion( self, sx, sy, ex, ey, depth=0 ) :
        if ex-sx < 2 or ey-sy < 2 : return
        hm = self.hm
        def rand( x ) :
            from random import random
            return x/2. - random() * x

        mid = hm[(sy+ey)/2][(sx+ex)/2] = ( hm[sy][sx] + hm[sy][ex] + hm[ey][sx] + hm[ey][ex]) / 4. + rand(3);
        sum = 2*mid + hm[sy][sx] + hm[ey][sx] + 0 
        hm[(sy+ey)/2][sx] = sum/4 + rand(3)

        sum = 2*mid + hm[sy][ex]  + hm[ey][ex]
        hm[(sy+ey)/2][ex] = sum/4 + rand(3)

        sum = 2*mid + hm[sy][sx] + hm[sy][ex]
        hm[sy][(sx+ex)/2] = sum/4 + rand(3)

        sum = 2*mid + hm[ey][sx] + hm[ey][ex]
        hm[ey][(sx+ex)/2] = sum/4 + rand(3)

        self.recursion( sx, sy, (ex+sx)/2, (ey+sy)/2, depth+1 )
        self.recursion( (ex+sx)/2, sy, ex, (ey+sy)/2, depth+1 )
        self.recursion( sx, (ey+sy)/2, (ex+sx)/2, ey, depth+1 )
        self.recursion( (ex+sx)/2, (ey+sy)/2, ex, ey, depth+1 )

    def loadTexture( self ):
        textureSurface = image.load('grass512.jpg')
        self.texture=textureSurface.mipmapped_texture
        
    def generateGrid( self, a, b ):
        coords = ()
        colors = ()
        txtr = ()
        triglist = []
        normals = ()
        
        for z in range(b):
            for x in range(a):
                coords += (x, self.hm[z][x], z )
                normals += self.computeNormal2( z, x)
                txtr += ( z % 2, x % 2 )

                if z == 0 or x == 0:
                    continue
                # sude kolo: nad vlevo, vlevo a nad.
                # liche kolo: nad, vlevo a on 
                triglist.extend( [ (z-1)*b+x-1, z*b+x-1, (z-1)*b+x] )
                triglist.extend( [ (z-1)*b+x, z*b+x-1, (z)*b+x ] )

        self.saveNormalMap( normals, "nm_last" )
        self.vertex_list = pyglet.graphics.vertex_list_indexed( len(coords)/3,
            triglist,
            ('v3f', coords), 
            ('t2f', txtr),
            #('c3f', colors),
            ('n3f', normals) );

    def computeNormal( self, x, z ):
        '''
                    v = normalised(sum(v12, v23, v34, v41))     
                where
                    vij = normalised(vi x vj) // normalised cross product
            Here are 9 special cases to solve, 
            I -- II -- III
            |     |     |
            IV -- V -- VI
            |     |     |
            VII - VIII - IX 

            I will make universal algorithm
        '''
        a = self.a-1
        print "computeNormal: xz {} {}, a = {}".format( x, z, a)
        p0 = [-a/2 + x, self.hm[x][z], -a/2 + z ]
        vectors = []
        cross_vecs = []
        if x > 0 :
            vectors.append( [-a/2+x-1 - p0[0], self.hm[x-1][z]-p0[1], 0] )
        if x < a-1 :
            vectors.append( [-a/2+x+1 - p0[0], self.hm[x+1][z]-p0[1], 0] )
        if z > 0 :
            vectors.append( [0, self.hm[x][z-1]-p0[1], -a/2 + z-1 -p0[2]] )
        if z < a-1 :
            vectors.append( [0, self.hm[x+1][z]-p0[1], -a/2 + z+1 -p0[2]] )

        def cross(a, b):
            c = [a[1]*b[2] - a[2]*b[1],
                 a[2]*b[0] - a[0]*b[2],
                 a[0]*b[1] - a[1]*b[0]]
            return c
        def normalised( vec ):
            from math import sqrt
            x, y, z = vec
            l = sqrt( x*x + y*y + z*z )
            return (x/l, y/l, z/l)

        cross_vecs.append( cross( vectors[0], vectors[1] ) )
        if len( vectors ) >= 3 :
            cross_vecs.append( cross( vectors[1], vectors[2] ) )

        if len( vectors ) == 4 :
            cross_vecs.append( cross( vectors[2], vectors[3] ) )

        for i in range( len(cross_vecs) ) :
            cross_vecs[i] = normalised(cross_vecs[i])
        n = [0, 0, 0]
        for cv in cross_vecs :
            n[0] += cv[0]
            n[1] += cv[1]
            n[2] += cv[2]

        return normalised( n )

    def computeNormal2( self, x, z ):
        '''
            // # x y store the position for which we want to calculate the normals
            // # height() here is a function that return the height at a point in the terrain

            // read neightbor heights using an arbitrary small offset
            vec3 off = vec3(1.0, 1.0, 0.0);
            float hL = height(P.xy - off.xz);
            float hR = height(P.xy + off.xz);
            float hD = height(P.xy - off.zy);
            float hU = height(P.xy + off.zy);

            // deduce terrain normal
            N.x = hL - hR;
            N.y = hD - hU;
            N.z = 2.0;
            N = normalize(N);
        '''
        a = self.a-1
        
        def cross(a, b):
            c = [a[1]*b[2] - a[2]*b[1],
                 a[2]*b[0] - a[0]*b[2],
                 a[0]*b[1] - a[1]*b[0]]
            return c
        def normalised( vec ):
            from math import sqrt
            x, y, z = vec
            l = sqrt( x*x + y*y + z*z )
            return (x/l, y/l, z/l)
        hl = self.height(x-1, z)
        hr = self.height(x+1, z)
        hd = self.height(x, z-1)
        hu = self.height(x, z+1)
        n = [ hl-hr, hd-hu, 2.0 ]
        return normalised( n )

    def setMaterial(self):
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(.34, .34, .0, 1))
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, vec(.2, .2, .3, 1))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec(0.6, 0.6, 0.6, 1))
        glMaterialfv(GL_FRONT, GL_COLOR_INDEXES, vec(0.5, 1, 1))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 45)

    def draw( self ) :
        self.setMaterial()
        glBindTexture( GL_TEXTURE_2D, self.texture.id)
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_NEAREST )
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR )

        self.vertex_list . draw( pyglet.gl.GL_TRIANGLES )

    def height( self, x, z ):
        from math import floor, ceil
        a = self.a
        #x, z = x + a/2, z + a/2
        print x, z
        if x < 0 or x >= a-1 or z < 0 or z >= a-1 :
            return 10
        
        # vysky okolnich bodu
        zf = int( floor(z) )
        xf = int( floor(x) )

        dx = x - xf
        dz = z - zf

        h1 = self.hm[zf][xf]
        h2 = self.hm[zf][xf+1]
        h3 = self.hm[zf+1][xf]
        h4 = self.hm[zf+1][xf+1]

        if dx*dx + dz*dz > (1-dx)*(1-dx) + (1-dz)*(1-dz) :
            dx = 1-dx
            dz = 1-dz
            h1 = h4
            h2, h3 = h3, h2
      
        if dz == 0 :
            height = h1 + (h2-h1)*dx
            return height
        
        l = 1./(dx+dz)
        htmp = h3 + (h2-h3)*(dx*l)
        height = h1 + (htmp-h1)/l
        return height
        

class Window(pyglet.window.Window):


    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        pyglet.clock.schedule_interval(self.update, 1./60)
        self.strafe = [0, 0]

        # Current (x, y, z) position in the world, specified with floats. Note
        # that, perhaps unlike in math class, the y-axis is the vertical axis.
        self.position = (12, 20, 12)
        self.cubPos = [12, 0, 12]

        # First element is rotation of the player in the x-z plane (ground
        # plane) measured from the z-axis down. The second is the rotation
        # angle from the ground plane up. Rotation is in degrees.
        #
        # The vertical plane rotation ranges from -90 (looking straight down) to
        # 90 (looking straight up). The horizontal rotation range is unbounded.
        self.rotation = (0, 0)
        self.reticle = None
        
        self.t = Terrain(33,33,generate=False)
        self.spin = 180
        self.fps = pyglet.clock.ClockDisplay()
        
        textureSurface = image.load('water1024.jpg')
        self.sea_tex = textureSurface.get_mipmapped_texture()

        self.color_coef = 1.0

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
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x + strafe)
            m = math.cos(y_angle)
            dy = math.sin(y_angle)
            if self.strafe[1]:
                # Moving left or right.
                dy = 0.0
                m = 1
            if self.strafe[0] > 0:
                # Moving backwards.
                dy *= -1
            # When you are flying up or down, you have less left and right
            # motion.
            dx = math.cos(x_angle) * m
            dz = math.sin(x_angle) * m
            # else:
            #     dy = 0.0
            #     dx = math.cos(x_angle)
            #     dz = math.sin(x_angle)
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

    def on_drawx( self ):
        self.clear()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.set_3d()
        #if not WIREFRAME : self.drawChessDesk()
        glColor3f(.15, .295, .055)
        glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, 1, 0, -1.5))
        glEnable(GL_CLIP_PLANE0)
        self.t.draw()

        glPushMatrix()
        glScalef(1, -1, 1)
        glTranslatef(0,-3.,0)
        glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, 1, 0, -1.5))
        glEnable(GL_CLIP_PLANE0)
        glColor4f(0.4, 0.4, 0.4, 1)
        self.t.draw()
        glPopMatrix()
        glDisable(GL_CLIP_PLANE0)
        if not WIREFRAME : self.drawSeaLevel()
        

        self.set_2d()
        glPopMatrix()
        
        glColor3d(0, 0, 0)
        #quad( 20, 20, (0,0,0) ) . draw( pyglet.gl.GL_TRIANGLES );
        self.fps.draw()
        pass

    def on_draw(self):
        glFogf(GL_FOG_START, width * 2 / 3)
        glFogf(GL_FOG_END, width)
        self.clear()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)  
        self.water_line = 1.5
        self.water_color = (0.3,0.3,1,1)
        
        #glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.set_3d()
        
        # kostka
        self.kostka_draw()

        if self.position[1] < self.water_line :
            #glEnable(GL_STENCIL_TEST)
            #glStencilFunc(GL_ALWAYS, 1, 1)
            #glStencilOp(GL_KEEP, GL_INCR, GL_INCR)
            glFogfv(GL_FOG_COLOR, (ctypes.c_float * 4)(*self.water_color))
            glFogi(GL_FOG_MODE, GL_EXP)
            glFogf(GL_FOG_DENSITY, 0.02)
            glFogf(GL_FOG_START, 0)
            glFogf(GL_FOG_END, width * 4 / 5)
            glEnable(GL_FOG)
        glPushAttrib(GL_STENCIL_BUFFER_BIT | GL_TRANSFORM_BIT | GL_CURRENT_BIT)
        # Draw the terrain above water
        glColor3f(.3, .59, .11)
        glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, 1, 0, -self.water_line))
        glEnable(GL_CLIP_PLANE0)
        self.t.draw()
        glDisable(GL_FOG)
        
        # Draw the reflection and create a stencil mask
        glPushAttrib(GL_FOG_BIT)
        glPushAttrib(GL_LIGHTING_BIT)
        glEnable(GL_STENCIL_TEST)
        glStencilFunc(GL_ALWAYS, 1, 1)
        glStencilOp(GL_KEEP, GL_INCR, GL_INCR)
        # Use fog to make the reflection less perfect
        glFogfv(GL_FOG_COLOR, (ctypes.c_float * 4)(*self.water_color))
        glFogi(GL_FOG_MODE, GL_EXP)
        glFogf(GL_FOG_DENSITY, 0.02)
        glFogf(GL_FOG_START, 0)
        glFogf(GL_FOG_END, width * 4 / 5)
        glEnable(GL_FOG)
        glPushMatrix()
        glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, -1, 0, self.water_line))
        glLightfv(GL_LIGHT0, GL_POSITION, vec(0, -100, 0, 0))
        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, vec(0, 1, 0, 0))
        glTranslatef(0, self.water_line * 2, 0)
        glScalef(1, -1, 1)
        glColor3f(1, 1, 1)
        c=self.color_coef
        glColor3f(.3*c, .59*c, .71*c)
        #glColor4f(0.26, 0.32, .6, 1)
        glFrontFace(GL_CW) # This assumes default front face is wound CCW
        if self.position[1] > self.water_line :
            self.t.draw()
        glFrontFace(GL_CCW)
        glPopMatrix()
        glPopAttrib()

        # Draw underwater terrain, except where masked by reflection
        # Use dense fog for underwater effect
        glFogi(GL_FOG_MODE, GL_EXP)
        glFogf(GL_FOG_DENSITY, 0.4)
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, -1, 0, self.water_line))
        glStencilFunc(GL_EQUAL, 0, -1)
        self.t.draw()
        glPopAttrib()

        glDisable(GL_CLIP_PLANE0)
        
        if not WIREFRAME : self.drawSeaLevel()

        glPopAttrib()
        glPopMatrix()

        self.set_2d()
        glColor3d(0, 0, 0)
        self.fps.draw()

    def kostka_draw(self):
        glDisable(GL_CLIP_PLANE0)
        glColor3f(0,0,1)
        x, y, z = self.cubPos
        y = self.t.height(x, z)
        from math import floor
        xf = int( floor(x) )
        zf = int( floor(z) )
        
        sizes = (GLfloat*10)()
        step = (GLfloat*1)()
        glGetFloatv(GL_POINT_SIZE_RANGE,sizes);
        glGetFloatv(GL_POINT_SIZE_GRANULARITY, step);
        curSize = sizes[0] + 5*step[0]
        glPointSize(curSize);
    
        glBegin(GL_POINTS)
        # (x, self.hm[z][x], z )
        glVertex3f(xf  , self.t.hm[zf  ][xf  ], zf  )
        glVertex3f(xf+1, self.t.hm[zf  ][xf+1], zf  )
        glVertex3f(xf  , self.t.hm[zf+1][xf  ], zf+1)
        glVertex3f(xf+1, self.t.hm[zf+1][xf+1], zf+1)
        glColor3f(1,0,0)

        glEnd()
        glTranslatef(x, y, z)
        glutSolidCube(0.1)
        glTranslatef(-x, -y, -z)

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
        rx, ry = self.rotation
        glPushMatrix()
        glRotatef(rx, 0, 1, 0)
        glRotatef(-ry, math.cos(math.radians(rx)), 0, math.sin(math.radians(rx)))
        x, y, z = self.position
        #y = self.t.height(x, z)
        #self.position = x, y, z
        glTranslatef(-x, -y, -z)

        self.spin += 1
        self.spin %= 360
        glPushMatrix();
        glTranslatef(0, 20, 0)
        glRotated(self.spin, 0.0, 1.0, 0.0);
        def vec(*args):
            return (GLfloat * len(args))(*args)

        glTranslated (0.0, 0.0, 6.0);
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

    def setSeaMaterial(sefl) :
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(.34, .34, .0, 1))
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, vec(.3, .3, .2, 1))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec(0.6, 0.6, 0.6, 1))
        #glMaterialfv(GL_FRONT, GL_COLOR_INDEXES, vec(1.0, 1, 1))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 105)

    def drawSeaLevel( self ) :
        self.setSeaMaterial()
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glBindTexture( GL_TEXTURE_2D, self.sea_tex.id)
        
        glBegin(GL_TRIANGLES)    
        glColor4f(0.1,0.6,.6,0.4)
        #glColor4f(.1,.3,0.6, 0.9)
        #glColor4f(.0,.0,0.0, 0.4)
        a = 10
        for z in xrange( -30, 30, a ) : 
            for x in xrange( -30, 30, a ) :

                glNormal3f(0,1,0)
                glTexCoord2i(1,1)
                glVertex3f(x + a, 1.5, z + a) 
                glNormal3f(0,1,0)
                glTexCoord2i(0,0)
                glVertex3f(x + 0, 1.5, z + 0)
                glNormal3f(0,1,0)
                glTexCoord2i(0,1)
                glVertex3f(x + 0, 1.5, z + a) 

                glNormal3f(0,1,0)
                glTexCoord2i(0,0)
                glVertex3f(x + 0, 1.5, z + 0)  
                glNormal3f(0,1,0)
                glTexCoord2i(1,1)
                glVertex3f(x + a, 1.5, z + a)
                glNormal3f(0,1,0)
                glTexCoord2i(1,0)
                glVertex3f(x + a, 1.5, z + 0)    

        glEnd()
        glDisable(GL_BLEND);

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
    #@window.event
    def vec(*args):
        return (GLfloat * len(args))(*args)
    def on_key_press( self, symbol, modifier ):
        global piece, bottom

        if symbol == key.A:
            self.strafe[1] -= 1
            print( "LEFT" )
        elif symbol == key.W:
            self.strafe[0] -= 1
            print( "UP" )
        elif symbol == key.S:
            self.strafe[0] += 1
            print( "DOWN" )
        elif symbol == key.D:
            self.strafe[1] += 1
            print( "RIGHT" )

        elif symbol == key.UP :
            self.cubPos[0] += .1
        elif symbol == key.DOWN :
            self.cubPos[0] -= .1 
        elif symbol == key.LEFT :
            self.cubPos[2] += .1
        elif symbol == key.RIGHT :
            self.cubPos[2] -= .1

        elif symbol == key.F :
            global WIREFRAME
            WIREFRAME = not WIREFRAME
            if WIREFRAME :
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            else :
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        elif symbol == key.N :
            self.t = Terrain(33,33)
        elif symbol == key.Q :
            exit(0)
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.O :
            self.color_coef += 0.1
        elif symbol == key.P :
            self.color_coef -= .1

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
    diffuse0 = vec(1.0,1.0,1.0,1.0)
    ambient0 = vec(1.0,1.0,1.0,1.0)
    specular0 = vec(1.0,1.0,1.0,1.0)
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
