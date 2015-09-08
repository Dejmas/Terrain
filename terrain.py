#!/usr/bin/python
import pyglet
from pyglet.window import key
from pyglet import image
from pyglet.gl import *
from OpenGL.GLUT import *
import math
from math import sqrt
from shader import Shader
width = 800
#height = 600

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
            a           - size of terrain 2^k + 1, like 17, 33, ...
            generate    - set true if you want new terrain or false to load last.
            water_line  - height of sea level  
    '''
    def __init__(self, a=33, water_line=1.5, generate=True) :
        self.a = a
        self.water_line = water_line
        self.water_color = (0.3,0.3,1,1)

        if generate :
            self.generateHeightMap(a, a)
            self.saveHeightMap('hm_last')
        else:
            self.loadHeighMap('hm_last')
        self.loadShader()
        self.loadTexture()
        self.generateGrid(a-1,a-1)

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
                hm[j/4][i /img.width/4] = toLoad( h )

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

    def loadShader(self):
        self.shader = None
        with open("shader.vs") as vsf:
            with  open("shader.fs") as fsf:
                self.shader = Shader(vs=vsf.read(), fs=fsf.read())
                #self.shader.Use()

    def loadTexture( self ):
        textureSurface = image.load('multicolor512.png')
        self.text0 = textureSurface.get_mipmapped_texture()

        textureSurface = image.load('grass512.jpg')
        self.text1 = textureSurface.get_mipmapped_texture()

        textureSurface = image.load('stone512.jpg')
        self.text2 = textureSurface.get_mipmapped_texture()

        textureSurface = image.load('snow512.png')
        self.text3 = textureSurface.get_mipmapped_texture()

        textureSurface = image.load('water1024.jpg')
        self.sea_tex = textureSurface.get_mipmapped_texture()
        
    def generateGrid( self, a, b ):
        coords = ()
        colors = ()
        txtr = ()
        txtr2 = ()
        triglist = []
        normals = ()
        s = 1./a
        
        for z in range(b):
            for x in range(a):
                coords += (x, self.hm[z][x], z )
                normals += (0, 1, 0)#self.computeNormal2( z, x)
                txtr += ( z % 2, x % 2 )
                txtr2 += ( z*s + (z%2)*s, x*s + (x%2)*s)

                if z == 0 or x == 0:
                    continue
                # sude kolo: nad vlevo, vlevo a nad.
                # liche kolo: nad, vlevo a on 
                triglist.extend( [ (z-1)*b+x-1, z*b+x-1, (z-1)*b+x] )
                triglist.extend( [ (z-1)*b+x, z*b+x-1, (z)*b+x ] )

        self.saveNormalMap( normals, "nm_last" )
        self.vertex_list = pyglet.graphics.vertex_list_indexed( 
            len(coords)/3,
            triglist,
            ('v3f', coords), 
            ('0t2f', txtr2),
            ('1t2f', txtr),
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
        #glMaterialfv(GL_FRONT, GL_COLOR_INDEXES, vec(0.5, 1, 1))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 45)
        #glColor4f(0.1,0.6,.6,0.4)
        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0); 
        glBindTexture(GL_TEXTURE_2D, self.text0.id); 
        glActiveTexture(GL_TEXTURE1); 
        glBindTexture(GL_TEXTURE_2D, self.text1.id);
        glActiveTexture(GL_TEXTURE2); 
        glBindTexture(GL_TEXTURE_2D, self.text2.id);
        glActiveTexture(GL_TEXTURE3); 
        glBindTexture(GL_TEXTURE_2D, self.text3.id);
        self.shader.uniformi("blendTexture", 0) 
        self.shader.uniformi("text1", 1)
        self.shader.uniformi("text2", 2)
        self.shader.uniformi("text3", 3)

    def drawHeightGrid( self ) :
        self.shader.Use()
        self.setMaterial()
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_NEAREST )
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR )

        self.vertex_list . draw( pyglet.gl.GL_TRIANGLES )
        self.shader.Unuse()
        glDisable(GL_TEXTURE_2D)
        #for t in (GL_TEXTURE1, GL_TEXTURE2, GL_TEXTURE3):
        #    glDisable(t)

    def draw( self, cam_height ):
        # Draw the terrain above water
        if cam_height < self.water_line :
            glFogfv(GL_FOG_COLOR, vec(*self.water_color))
            glFogi(GL_FOG_MODE, GL_EXP)
            glFogf(GL_FOG_DENSITY, 0.02)
            glFogf(GL_FOG_START, 0)
            #glFogf(GL_FOG_END, width * 4 / 5)
            glEnable(GL_FOG)
        glPushAttrib(GL_STENCIL_BUFFER_BIT | GL_TRANSFORM_BIT | GL_CURRENT_BIT)
        glColor3f(.3, .59, .11)
        glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, 1, 0, -self.water_line))
        glEnable(GL_CLIP_PLANE0)
        self.drawHeightGrid()
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
        #glFogf(GL_FOG_END, width * 4 / 5)
        glEnable(GL_FOG)
        glPushMatrix()
        glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, -1, 0, self.water_line))
        glLightfv(GL_LIGHT0, GL_POSITION, vec(0, -100, 0, 0))
        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, vec(0, 1, 0, 0))
        glTranslatef(0, self.water_line * 2, 0)
        glScalef(1, -1, 1)
        glColor3f(.3, .59, .71)
        #glColor4f(0.26, 0.32, .6, 1)
        
        #  
        glFrontFace(GL_CW) 
        if cam_height > self.water_line :
            self.drawHeightGrid()
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
        self.drawHeightGrid()
        glDisable(GL_CLIP_PLANE0)
        glPopAttrib()
        self.drawSeaLevel()
        glPopAttrib()

    def setSeaMaterial(sefl) :
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(.34, .34, .0, 1))
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, vec(.3, .3, .2, 1))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec(0.6, 0.6, 0.6, 1))
        #glMaterialfv(GL_FRONT, GL_COLOR_INDEXES, vec(1.0, 1, 1))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 105)

    def drawSeaLevel( self ) :
        self.setSeaMaterial()
        glEnable(GL_BLEND);
        glDisable(GL_CULL_FACE)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glActiveTexture( GL_TEXTURE0 )
        glBindTexture( GL_TEXTURE_2D, self.sea_tex.id)

        
        glBegin(GL_TRIANGLES)    
        glColor4f(0.1,0.6,.6,0.8)

        #glColor4f(.1,.3,0.6, 0.9)
        #glColor4f(.0,.0,0.0, 0.4)
        a = self.a
        y = self.water_line
        s = 2
        for z in xrange( 0, a, s ) : 
            for x in xrange( 0, a, s ) :

                glNormal3f(0,1,0)
                glTexCoord2i(1,1)
                glVertex3f(x + s, y, z + s) 
                glNormal3f(0,1,0)
                glTexCoord2i(0,0)
                glVertex3f(x + 0, y, z + 0)
                glNormal3f(0,1,0)
                glTexCoord2i(0,1)
                glVertex3f(x + 0, y, z + s) 

                glNormal3f(0,1,0)
                glTexCoord2i(0,0)
                glVertex3f(x + 0, y, z + 0)  
                glNormal3f(0,1,0)
                glTexCoord2i(1,1)
                glVertex3f(x + s, y, z + s)
                glNormal3f(0,1,0)
                glTexCoord2i(1,0)
                glVertex3f(x + s, y, z + 0)    

        glEnd()
        glDisable(GL_BLEND);
        glEnable(GL_CULL_FACE)
        

    def height( self, x, z ):
        from math import floor, ceil
        a = self.a
        
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

    def Height( self, x, z, floating=False ):
        h = self.height(x, z)
        if not floating : return h
        if h < self.water_line: return self.water_line
        return h
