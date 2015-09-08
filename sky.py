#!/usr/bin/env python
import os
import pyglet
from pyglet.gl import *

class SkyBox:

	r = 5.0
	coords = [
		(( r, -r, -r), ( r,  r, -r), (-r,  r, -r), (-r, -r, -r)), # ft
		((-r, -r,  r), (-r,  r,  r), ( r,  r,  r), ( r, -r,  r)), # bk
		((-r, -r, -r), (-r,  r, -r), (-r,  r,  r), (-r, -r,  r)), # lt
		(( r, -r,  r), ( r,  r,  r), ( r,  r, -r), ( r, -r, -r)), # rt
		(( r,  r,  r), (-r,  r,  r), (-r,  r, -r), ( r,  r, -r),), # up
		((-r, -r,  r), ( r, -r,  r), ( r, -r, -r), (-r, -r, -r)), # dn
	]

	def __init__(self, textures):
		self.texcoords = [(tex, coord) 
			for tex, coord in zip(textures, self.coords)
			if tex is not None]
		assert self.texcoords, 'No skybox textures found'

	file_suffixes = (
		'_right',  
		'_left', 
		'_back', 
		'_front', 
		'_top', 
		'_bottom',
		)
	
	@classmethod
	def fromDir(cls, dirpath, file_prefix='', file_ext='.jpg'):
		assert os.path.isdir(dirpath), 'Invalid directory path: %s' % dirpath
		print dirpath
		print "prefix", file_prefix
		textures = []
		for suffix in cls.file_suffixes:
			filepath = os.path.join(dirpath, '%s%s%s' % (file_prefix, suffix, file_ext))
			if os.path.exists(filepath):
				textures.append(pyglet.image.load(filepath).texture)
			else:
				textures.append(None)
		print textures
		return cls(textures)
	
	def draw(self, xrot=0.0, yrot=0.0):
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_LIGHTING)
		glColor3f(1.0, 1.0, 1.0)
		glPushMatrix()
		glLoadIdentity()
		glRotatef(xrot, 1.0, 0.0, 0.0)
		glRotatef(yrot, 0.0, 1.0, 0.0)

		for texture, (p1, p2, p3, p4) in self.texcoords:
			glEnable(texture.target)
			glBindTexture(texture.target, texture.id)
			glTexParameteri(texture.target, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
			glTexParameteri(texture.target, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
			glBegin(GL_QUADS)
			glTexCoord2f(0.0, 0.0)
			glVertex3f(*p1)
			glTexCoord2f(0.0, 1.0)
			glVertex3f(*p2)
			glTexCoord2f(1.0, 1.0)
			glVertex3f(*p3)
			glTexCoord2f(1.0, 0.0)
			glVertex3f(*p4)
			glEnd()

		glPopMatrix()
		glPopAttrib()


if __name__ == '__main__':
	import sys
	global xrot, yrot, win
	win = pyglet.window.Window(width=800, height=600, resizable=True, visible=False)
	skybox = SkyBox.fromDir(os.path.dirname(sys.argv[1]), os.path.basename(sys.argv[1]))
	xrot = yrot = 0

	def on_resize(width, height):
		glViewport(0, 0, width, height)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluPerspective(70, 1.0*width/height, 0.1, 1000.0)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
	win.on_resize = on_resize

	@win.event
	def on_mouse_motion(x, y, dx, dy):
		global xrot, yrot
		yrot += dx * 0.3
		xrot += dy * 0.3

	@win.event
	def on_draw():
		global xrot, yrot
		glClear(GL_COLOR_BUFFER_BIT)
		skybox.draw(xrot, yrot)
	
	win.set_visible()
	win.set_exclusive_mouse()
	pyglet.app.run()
