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
SHADER = True
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
        self.dlists = {}
        self.water_line = water_line - 0.15
        self.water_color = (.1,.3,0.6,1)
        self.lightPos = (0, 0, 0)
        self.lightRotation = 0
        self.waveTime = 0
        self.waveWidth = 0.7
        self.waveHeight = 0.25
        if generate :
            self.generateHeightMap(a, a)
            self.saveHeightMap('hm_last')
        else:
            self.loadHeighMap('hm_last')
        if SHADER: self.loadShader()
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
        self.gridShader = None
        with open("shaders/heightGrid.vs") as vsf:
            with  open("shaders/heightGrid.fs") as fsf:
                self.gridShader = Shader(vs=vsf.read(), fs=fsf.read())

        with open("shaders/water.vs") as vsf:
            with  open("shaders/water.fs") as fsf:
                self.waterShader = Shader(vs=vsf.read(), fs=fsf.read())

    def loadTexture( self ):
        textureSurface = image.load('data/multicolor512.png')
        self.text0 = textureSurface.get_mipmapped_texture()

        textureSurface = image.load('data/grass512.jpg')
        self.text1 = textureSurface.get_mipmapped_texture()

        textureSurface = image.load('data/sand512.png')
        self.text2 = textureSurface.get_mipmapped_texture()

        textureSurface = image.load('data/stone512.jpg')
        self.text3 = textureSurface.get_mipmapped_texture()

        textureSurface = image.load('data/water1024.jpg')
        self.sea_tex = textureSurface.get_mipmapped_texture()
        
    def generateGrid( self, a, b ):
        coords = ()
        txtr = ()
        txtr2 = ()
        triglist = []
        normals = ()
        s = 1./a
        
        for z in range(b):
            for x in range(a):
                coords += (x, self.hm[z][x], z )
                normals += self.computeNormal( z, x)
                txtr += ( z % 2, x % 2 )
                txtr2 += ( z*s , x*s )

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
                  v3
                  ^
                  |      
          v0 < -- p0 -- > v2
                  |      
                  V
                  v2 
            find vetors to adjecent vertexes
            n = normalised(sum(v12, v23, v34, v41))     
                where
                    vij = normalised(vi x vj) # normalised cross product 
        '''
        a = self.a-1
        # (x, self.hm[z][x], z )
        p0 = [ x, self.hm[z][x], z ]
        cross_vecs = []
        v0 = [-1, 0, 0 ]
        if x > 0 :
            v0[1] =  -p0[1]+self.hm[z][x-1]
        v1 = [0, 0, -1 ]
        if z > 0 :
            v1[1] = -p0[1]+self.hm[z-1][x]
        v2 = [1, 0, 0 ]
        if x < a-1 :
            v2[1] = -p0[1]+self.hm[z][x+1]
        v3 = [0, 0, 1 ]
        if z < a-1 :
            v3[1] = -p0[1]+self.hm[z][x+1]


        def cross(a, b):
            c = [a[1]*b[2] - a[2]*b[1],
                 a[2]*b[0] - a[0]*b[2],
                 a[0]*b[1] - a[1]*b[0]]
            return c
        def normalised( vec ):
            from math import sqrt
            x, y, z = vec
            l = sqrt( x*x + y*y + z*z )
            if not l : return (0, 0, 0)
            return (x/l, y/l, z/l)

        cross_vecs.append( cross( v1, v0 ) )
        cross_vecs.append( cross( v2, v1 ) )
        cross_vecs.append( cross( v3, v2 ) )
        cross_vecs.append( cross( v0, v3 ) )

        for i in range( len(cross_vecs) ) :
            cross_vecs[i] = normalised(cross_vecs[i])
        n = [0, 0, 0]
        for cv in cross_vecs :
            n[0] += cv[0]
            n[1] += cv[1]
            n[2] += cv[2]

        return normalised( n )

    def setMaterial(self):
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
        glEnable(GL_DEPTH_TEST);
        glDepthFunc(GL_LEQUAL);
        glShadeModel(GL_SMOOTH);
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(.34, .34, .34, 1))
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, vec(.3, .3, .3, 1))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec(0.6, 0.6, 0.6, 1))
        glMaterialfv(GL_FRONT, GL_COLOR_INDEXES, vec(0.5, 1, 1))
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
    
        def m3dTransformVector3(vOut3f, v3f, m33f):
            vOut3f[0] = m33f[0] * v3f[0] + m33f[4] * v3f[1] + m33f[8] *  v3f[2] + m33f[12]
            vOut3f[1] = m33f[1] * v3f[0] + m33f[5] * v3f[1] + m33f[9] *  v3f[2] + m33f[13]
            vOut3f[2] = m33f[2] * v3f[0] + m33f[6] * v3f[1] + m33f[10] * v3f[2] + m33f[14]

        lightPos0Eye = [0,0,0,0]
        mv = (GLfloat * 16)()
        glPushMatrix();
        self.lightRotation = (self.lightRotation + 0.3) % 360;
        glRotatef(self.lightRotation, 0.0, 0.0, 1.0);
        glGetFloatv(GL_MODELVIEW_MATRIX, mv);
        m3dTransformVector3(lightPos0Eye, vec(50, 100, 50), mv);
        glPopMatrix();

        if SHADER:
            self.gridShader.uniformi("blendTexture", 0) 
            self.gridShader.uniformi("text1", 1)
            self.gridShader.uniformi("text2", 2)
            self.gridShader.uniformi("text3", 3)
            #self.gridShader.uniformf("lightPos[0]", *lightPos0Eye[:3])
            #self.gridShader.uniformf("density", 1 )

    def drawHeightGrid( self ) :
        if SHADER: self.gridShader.Use()
        self.setMaterial()
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_NEAREST )
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR )
        if not 'terrain' in self.dlists :
            self.dlists['terrain'] = glGenLists(1)
            glNewList(self.dlists['terrain'], GL_COMPILE )
            self.vertex_list . draw( pyglet.gl.GL_TRIANGLES )
            glEndList()

        glCallList(self.dlists['terrain'])
        if SHADER: self.gridShader.Unuse()
        glDisable(GL_TEXTURE_2D)

    def draw( self, cam_height ):
        glFogf(GL_FOG_DENSITY, 0)
        # Draw the terrain above water
        if cam_height < self.water_line :
            glFogfv(GL_FOG_COLOR, vec(*self.water_color))
            glFogf(GL_FOG_DENSITY, .1)
            glEnable(GL_FOG)
        glPushAttrib(GL_STENCIL_BUFFER_BIT | GL_TRANSFORM_BIT | GL_CURRENT_BIT)
        glColor3f(.3, .59, .11)
        glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, 1, 0, -self.water_line))
        glEnable(GL_CLIP_PLANE0)
        self.drawHeightGrid()
        glDisable(GL_FOG)
        
        # # Draw the reflection and create a stencil mask
        # glPushAttrib(GL_FOG_BIT)
        # glPushAttrib(GL_LIGHTING_BIT)
        # glEnable(GL_STENCIL_TEST)
        # glStencilFunc(GL_ALWAYS, 1, 1)
        # glStencilOp(GL_KEEP, GL_INCR, GL_INCR)
        # # Use fog to make the reflection less perfect
        # glFogfv(GL_FOG_COLOR, (ctypes.c_float * 4)(*self.water_color))
        # glFogf(GL_FOG_DENSITY, .1)
        # glEnable(GL_FOG)
        # glPushMatrix()
        # glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, -1, 0, self.water_line))
        # glLightfv(GL_LIGHT0, GL_POSITION, vec(0, -100, 0, 0))
        # glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, vec(0, 1, 0, 0))
        # glTranslatef(0, self.water_line * 2, 0)
        # glScalef(1, -1, 1)
        # glColor3f(.3, .59, .71)
        # #glColor4f(0.26, 0.32, .6, 1)
        
        #  
        # glFrontFace(GL_CW) 
        # if cam_height > self.water_line :
        #     self.drawHeightGrid()
        # glFrontFace(GL_CCW)
        # glPopMatrix()
        # glPopAttrib()

        # Draw underwater terrain, except where masked by reflection
        # Use dense fog for underwater effect
        # if camera is under water increase fog density
        if cam_height < self.water_line :
            glFogf(GL_FOG_DENSITY, 0.7)
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, -1, 0, self.water_line))
        glStencilFunc(GL_EQUAL, 0, -1)
        self.drawHeightGrid()
        glFogf(GL_FOG_DENSITY, 0)
        glDisable(GL_CLIP_PLANE0)
        glPopAttrib()
        self.drawSeaLevel()
        #glPopAttrib()

    def setSeaMaterial(self) :
        glClearColor(0, 0, .0, 1)

        glEnable(GL_DEPTH_TEST);
        glEnable(GL_CULL_FACE)
        #glDepthFunc(GL_LEQUAL);
        glShadeModel(GL_SMOOTH);
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(.7, .7, .8, 1))
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, vec(.7, .7, .8, 1))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec(1, 1, 1, 1))
        #glMaterialfv(GL_FRONT, GL_COLOR_INDEXES, vec(1.0, 1, 1))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 105)

        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glActiveTexture( GL_TEXTURE0 )
        glBindTexture( GL_TEXTURE_2D, self.sea_tex.id)
        glColor4f(.1,.3,0.6, 0.7)
        if SHADER :
            self.waveTime += 0.025
            self.waterShader.uniformi("tex0", 0 )
            self.waterShader.uniformf("waveTime", self.waveTime )
            self.waterShader.uniformf("waveWidth", self.waveWidth )
            self.waterShader.uniformf("waveHeight", self.waveHeight )

    def drawSeaLevel( self ) :
        if SHADER : self.waterShader.Use()
        self.setSeaMaterial()
        if not 'water' in self.dlists:
            self.dlists['water'] = glGenLists(1)
            glNewList(self.dlists['water'], GL_COMPILE)
            glBegin(GL_TRIANGLES)    
            s = 1./33
            a = self.a
            y = self.water_line+self.waveHeight
            s = 1

            for z in xrange( -a, a, s ) : 
                for x in xrange( -a, a, s ) :

                    glNormal3f(0,1,0)
                    glTexCoord2i(1, 1)
                    glVertex3f(x +1, y, z +1) 
                    glNormal3f(0,1,0)
                    glTexCoord2i(0, 0)
                    glVertex3f(x + 0, y, z + 0)
                    glNormal3f(0,1,0)
                    glTexCoord2i(0, 1)
                    glVertex3f(x + 0, y, z +1) 

                    glNormal3f(0,1,0)
                    glTexCoord2i(0, 0)
                    glVertex3f(x + 0, y, z + 0)  
                    glNormal3f(0,1,0)
                    glTexCoord2i(1, 1)
                    glVertex3f(x +1, y, z +1)
                    glNormal3f(0,1,0)
                    glTexCoord2i(1, 0)
                    glVertex3f(x +1, y, z + 0)    

            glEnd()
            glEndList()
        glCallList(self.dlists['water'])
        if SHADER : self.waterShader.Unuse()
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



'''
    x
        glEnable(GL_LIGHTING);
        glEnable(GL_LIGHT0);
        glEnable(GL_NORMALIZE);
        # Light model parameters:
        # -------------------------------------------

        lmKa = vec(0.0, 0.0, 0.0, 0.0 )
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, lmKa);

        glLightModelf(GL_LIGHT_MODEL_LOCAL_VIEWER, 1.0);
        glLightModelf(GL_LIGHT_MODEL_TWO_SIDE, 0.0);

        # -------------------------------------------
        # Spotlight Attenuation

        spot_direction = vec(1.0, -1.0, 0.0 )
        spot_exponent = 30;
        spot_cutoff = 180;

        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, spot_direction);
        glLighti(GL_LIGHT0, GL_SPOT_EXPONENT, spot_exponent);
        glLighti(GL_LIGHT0, GL_SPOT_CUTOFF, spot_cutoff);

        Kc = 1.0;
        Kl = 0.0;
        Kq = 0.0;

        glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION,Kc);
        glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, Kl);
        glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, Kq);


        # ------------------------------------------- 
        # Lighting parameters:

        light_pos = vec(16.0, 10.0, 16.0, 1.0)
        light_Ka  = vec(1.0, 0.5, 0.5, 1.0)
        light_Kd  = vec(1.0, 0.1, 0.1, 1.0)
        light_Ks  = vec(1.0, 1.0, 1.0, 1.0)

        glLightfv(GL_LIGHT0, GL_POSITION, light_pos);
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_Ka);
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_Kd);
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_Ks);

        # -------------------------------------------
        # Material parameters:

        material_Ka = vec(0.5, 0.0, 0.0, 1.0)
        material_Kd = vec(0.4, 0.4, 0.5, 1.0)
        material_Ks = vec(0.8, 0.8, 0.0, 1.0)
        material_Ke = vec(0.1, 0.0, 0.0, 0.0)
        material_Se = 20.0;

        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, material_Ka);
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, material_Kd);
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, material_Ks);
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, material_Ke);
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, material_Se);
'''