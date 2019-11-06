# Copyright Joni Hariyanto <ynjh d0t jo At gmail.com> http://jon1.us/P3D/
# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.

from __future__ import print_function
from __future__ import absolute_import

from menu import DropDownMenu, PopupMenu

import direct.directbase.DirectStart
from direct.gui.DirectGui import OnscreenText
from direct.showbase.DirectObject import DirectObject

from panda3d.core import getModelPath, ModifierButtons
from panda3d.core import NodePath, Texture, TextureStage
from panda3d.core import Vec3
from panda3d.core import RenderModeAttrib, RenderState

import os,sys

os.chdir(sys.path[0])

modelsPath=filter(lambda p: p.getBasename().find('models')>-1, [getModelPath().getDirectory(i) for i in range(getModelPath().getNumDirectories())])
getModelPath().appendPath(modelsPath[0].getFullpath()+'/maps')

thickness=1
gameSlots={}
for s in range(4):
    gameSlots[s]=None
TSmode=(TextureStage.MModulate,TextureStage.MBlend,TextureStage.MDecal)

def resetModButtons(win=None):
    if win is not None and not win.getProperties().getForeground():
       return
    origMB=ModifierButtons(base.buttonThrowers[0].node().getModifierButtons())
    origMB.allButtonsUp()
    base.buttonThrowers[0].node().setModifierButtons(origMB)

def func1():
    model.setR(model,-20)
    print('func 1')

def func2(a,b,c):
    model.setR(model,20)
    print('func 2 args :', a,b,c)

def func3():
    model.setScale(model,.8)
    print('func 3')

def func4():
    model.setScale(model,1.25)
    print('func 4')

def func5():
    model.clearTransform()
    print('func 5')

def addTexture(stage,path):
    tex=loader.loadTexture(path)
    tex.setWrapU(Texture.WMRepeat)
    tex.setWrapV(Texture.WMRepeat)
    s=str(stage)
    TS=model.findTextureStage(s)
    if not TS:
       TS=TextureStage(s)
       TS.setMode(TSmode[stage-2])
       TS.setSort(stage-1)
    model.setTexture(TS,tex)

def removeTexture(stage):
    TS=model.findTextureStage(str(stage))
    model.clearTexture(TS)

def newGame():
    global thickness
    thickness=1
    render.setState(RenderState.makeEmpty())
    model.setState(RenderState.makeEmpty())
    func5()
    print('NEW GAME')

def loadGame(slot):
    print('LOADED from slot',slot+1)

def saveGame(slot):
    gameSlots[slot]=1
    print('SAVED to slot',slot+1)

def changeThickness(t):
    global thickness
    thickness=t
    render.setRenderModeThickness(t)

def changeModel(newmodel):
    tempParent=NodePath('')
    newModel=loader.loadModel(newmodel)
    newModel.findAllMatches('**/+GeomNode').reparentTo(tempParent)
    tempParent.setScale(1.5/tempParent.getBounds().getRadius())
    tempParent.setPos(-tempParent.getBounds().getCenter())
    tempParent.flattenStrong()
    tempParent.find('**/+GeomNode').node().replaceNode(model.node())

def exit():
    Sequence(
       Func(gameMenu.destroy),
       model.scaleInterval(.3,model.getScale()*.005,blendType='easeIn'),
       Func(sys.exit)
    ).start()

def createGameMenuItems():
    return (
    ('_New',0,newGame),
    0, # separator
    ('_Load',0, [ ('slot %s'%(s+1),0,loadGame if gameSlots[s] else 0,s) for s in range(4) ] ),
    ('_Save',0, [ ('slot %s'%(s+1),0,saveGame,s) for s in range(4) ] ),
    0, # separator
    ('Prefe_rence',0,lambda:0),
    0, # separator
    ('E_xit>Escape','lilsmiley.rgba',exit),
    )

def createViewMenuItems():
    rms=[ (render.setRenderMode if render.getRenderMode()!=rm else 0,rm,thickness,0) \
             for rm in (RenderModeAttrib.MWireframe,
                        RenderModeAttrib.MFilled, RenderModeAttrib.MPoint)
        ]
    return (
    ('_Wireframe mode',0)+rms[0],
    ('_Filled mode',0)+rms[1],
    ('_Point mode',0)+rms[2],
    0, # separator
    ('_Thickness',0, [ ('_%s'%i,0,changeThickness if thickness!=i else 0,i) for i in range(1,10) ]),
    )

def createModelMenuItems():
    return (
    ('_Abstract room',0,changeModel,'samples/Normal-Mapping/models/abstractroom'),
    ('_Carousel',0,changeModel,'samples/Carousel/models/carousel_base'),
    ('_Eve',0,changeModel,'samples/Looking-and-Gripping/models/eve'),
    ('_Monster',0,changeModel,'samples/Motion-Trails/models/dancer'),
    ('Music _box',0,changeModel,'samples/Music-Box/models/MusicBox'),
    ('_Panda',0,changeModel,'panda-model'),
    ('_Ralph',0,changeModel,'samples/Roaming-Ralph/models/ralph'),
    ('_Smiley',0,changeModel,'smiley'),
    ('_TV man',0,changeModel,'samples/Teapot-on-TV/models/mechman_idle'),
    )

def createMenuMenuItems():
    effs=[ (0 if gameMenu.effect==X else setattr,gameMenu,'effect',X) \
             for X in (DropDownMenu.ENone, DropDownMenu.EFade,
                       DropDownMenu.ESlide, DropDownMenu.EStretch)
        ]
    algs=[ (0 if gameMenu.alignment==X else gameMenu.align,X) \
             for X in (DropDownMenu.ALeft,
                       DropDownMenu.ACenter, DropDownMenu.ARight)
        ]
    pos=[ (0 if gameMenu.edgePos==X else gameMenu.setEdgePos,X) \
             for X in (DropDownMenu.PLeft, DropDownMenu.PRight,
                       DropDownMenu.PBottom, DropDownMenu.PTop)
        ]
    return (
    ('_Effect',0, (
        ('_None',0)+effs[0],
        ('_Fade',0)+effs[1],
        ('_Slide',0)+effs[2],
        ('_Stretch',0)+effs[3],
    )),
    ('_Alignment',0, (
        ('_Left',0)+algs[0],
        ('_Center',0)+algs[1],
        ('_Right',0)+algs[2],
    )),
    ('_Position',0, (
        ('_Left',0)+pos[0],
        ('_Right',0)+pos[1],
        ('_Bottom',0)+pos[2],
        ('_Top',0)+pos[3],
        0, # separator
        ('you can also do this by\ndragging the menubar',0,0),
    )),
    (['_Draggable','Not _draggable'][gameMenu.isDraggable()],0,gameMenu.setDraggable,not gameMenu.isDraggable())
    )

def createHelpMenuItems():
    return (
    ('User _guide',0,lambda:0),
    0, # separator
    ('_Register',0,lambda:0),
    ('Report _problems',0,lambda:0),
    ('Request new _features',0,lambda:0),
    ('_Donate authors',0,lambda:0),
    0, # separator
    ('_About',0,lambda:0),
    )

def createContextMenu():
    myPopupMenu=PopupMenu(
       items=(
         # format :
         #   ( 'Item text', 'path/to/image', command, arg1,arg2,.... )
         # for hotkey, insert an underscore before the character
         ('Rotate 20 deg _CCW',0,func1),
         ('Rotate 20 deg C_W',0,func2, 0,1,2), # appends some arguments (0,1,2)
         0, # separator
         ('_Shrink>Ctrl+S','envir-tree2.png',func3),
         ('_Grow>Ctrl+G','envir-tree1.png',func4),
         0, # separator
         ('_Reset transform','envir-mountain1.png',func5),
         0, # separator
         ('Multitextures stage _2',0, (
             ('Grid','grid.rgb',addTexture,2,'grid.rgb'),
             ('Ground','envir-ground.jpg',addTexture,2,'envir-ground.jpg'),
             ('Rock','envir-rock1.jpg',addTexture,2,'envir-rock1.jpg'),
             ('Toontown map','4map.rgb',addTexture,2,'4map.rgb'),
             0, # separator
             ('_Clear',0,removeTexture if model.findTextureStage('2') else 0,2),
         )),
         ('Multitextures stage _3',0, (
             ('Noise','noise.rgb',addTexture,3,'noise.rgb'),
             ('Controls','shuttle_controls_1.rgb',addTexture,3,'shuttle_controls_1.rgb'),
             ('Text glyphs','cmtt12.rgb',addTexture,3,'cmtt12.rgb'),
             0, # separator
             ('_Clear',0,removeTexture if model.findTextureStage('3') else 0,3),
         )),
         ('Multitextures stage _4',0, (
             ('Tree','envir-tree2.png',addTexture,4,'envir-tree2.png'),
             ('Bamboo','envir-bamboo.png',addTexture,4,'envir-bamboo.png'),
             ('Mountain','envir-mountain2.png',addTexture,4,'envir-mountain2.png'),
             0, # separator
             ('_Clear',0,removeTexture if model.findTextureStage('4') else 0,4),
         )),
         ('Clear _multitextures',0,model.clearTexture if model.findAllTextureStages().getNumTextureStages()>1 else 0),
         0, # separator
         ('_dummy item1 to show hotkey cycle',0,lambda:0),
         ('_dummy item2 to show hotkey cycle>no shortcut',0,lambda:0),
         ('_dummy item3 to show hotkey cycle',0,lambda:0),
         0, # separator
         ("Multiple lines is possible.\n    The arrow is vertically aligned.\n        The _Underline is placed correctly.>this shortcut won't be displayed", 0, (
            ('The shortcut is also\n    vertically aligned>a fake SHORTcut',0,lambda:0),
            ('submenu\n    item #2>me too :p',0,lambda:0)
         )),
         0, # separator
         ('I have some submenus',0, (
            ('submenu item #1',0, (
               ('submenu #1 subsubmenu item #1',0,lambda:0),
               ('submenu #1 subsubmenu item #2',0,0),
            )),
            ('submenu item #2',0, (
               ('submenu #2 subsubmenu item #1',0,lambda:0),
               ('submenu #2 subsubmenu item #2',0,lambda:0),
               ('submenu #2 subsubmenu item #3',0, (
                  ('submenu #2 subsubmenu #3 subsubsubmenu item #1',0,lambda:0),
                  ('submenu #2 subsubmenu #3 subsubsubmenu item #2',0,lambda:0),
                  ('submenu #2 subsubmenu #3 subsubsubmenu item #3',0,lambda:0),
                  ('submenu #2 subsubmenu #3 subsubsubmenu item #4',0,lambda:0),
               )),
               # pass empty sequence to make a disabled item with submenu
               ('submenu #2 disabled subsubmenu item #4',0,[]),
            )),
            ('submenu item #3',0, (
               ('submenu #3 subsubmenu item #1',0,lambda:0),
               ('submenu #3 subsubmenu item #2',0,0),
               ('submenu #3 subsubmenu item #3',0,lambda:0),
               ('submenu #3 subsubmenu item #4',0,lambda:0),
               ('submenu #3 subsubmenu item #5',0,lambda:0),
               ('submenu #3 subsubmenu item #6',0,0),
               ('submenu #3 subsubmenu item #7',0,lambda:0),
            )),
         )),
         # pass empty sequence to make a disabled item with submenu
         ("But I'm disabled",0, []),
         # disabled items, pass 0 for the command
         ('_Disabled item>shortcut1','lilsmiley.rgba',0),
         0, # separator
         ('E_xit>Escape','lilsmiley.rgba',exit),
       ),
       #~ font=loader.loadFont('fonts/Medrano.ttf'),
       baselineOffset=-.35,
       scale=Vec3(.045, 0, .045), itemHeight=1.2, leftPad=.2,
       separatorHeight=.3,
       underscoreThickness=1,

       BGColor=(.9,.9,.8,.94),
       BGBorderColor=(.8,.3,0,1),
       separatorColor=(0,0,0,1),
       frameColorHover=(.3,.3,.3,1),
       frameColorPress=(0,1,0,.85),
       textColorReady=(0,0,0,1),
       textColorHover=(1,.7,.2,1),
       textColorPress=(0,0,0,1),
       textColorDisabled=(.65,.65,.65,1),

       # just another color scheme
       #~ BGColor=(0,0,0,.94),
       #~ BGBorderColor=(1,.85,.4,1),
       #~ separatorColor=(1,1,1,1),
       #~ frameColorHover=(1,.85,.4,1),
       #~ frameColorPress=(0,1,0,1),
       #~ textColorReady=(1,1,1,1),
       #~ textColorHover=(0,0,0,1),
       #~ textColorPress=(0,0,0,1),
       #~ textColorDisabled=(.5,.5,.5,1),
    )

def menuBarMoved():
    print('menuBarMoved')

model=loader.loadModel('smiley').find('**/+GeomNode')
model.reparentTo(render.attachNewNode('modelParent'))
model.setTransparency(1)
model.getParent().hprInterval(5,Vec3(360,0,0)).loop()

gameMenu = DropDownMenu(
    items=(
      ('_Game', createGameMenuItems),
      ('_View', createViewMenuItems),
      ('Mo_del', createModelMenuItems),
      ('_Menu', createMenuMenuItems),
      ('_Help', createHelpMenuItems)
    ),
    sidePad=.75,
    align=DropDownMenu.ALeft,
    #~ align=DropDownMenu.ACenter,
    #~ align=DropDownMenu.ARight,
    #~ effect=DropDownMenu.ESlide,
    effect=DropDownMenu.EStretch,
    #~ effect=DropDownMenu.EFade,
    edgePos=DropDownMenu.PTop,
    #~ edgePos=DropDownMenu.PBottom,
    #~ edgePos=DropDownMenu.PLeft,
    #~ edgePos=DropDownMenu.PRight,

    #~ font=loader.loadFont('fonts/Medrano.ttf'),
    baselineOffset=-.35,
    scale=.045, itemHeight=1.2, leftPad=.2,
    separatorHeight=.3,
    underscoreThickness=1,

    BGColor=(.9,.9,.8,.94),
    BGBorderColor=(.8,.3,0,1),
    separatorColor=(0,0,0,1),
    frameColorHover=(.3,.3,.3,1),
    frameColorPress=(0,1,0,.85),
    textColorReady=(0,0,0,1),
    textColorHover=(1,.7,.2,1),
    textColorPress=(0,0,0,1),
    textColorDisabled=(.65,.65,.65,1),
    draggable=True,
    onMove=menuBarMoved
 )

OnscreenText( parent=base.a2dBottomCenter,
              text='Right click to pop up a context menu', fg=(1,1,1,1),
              pos=(0,.02), scale=.045)

DO=DirectObject()
DO.accept('mouse3',createContextMenu)
DO.accept('control-s',func3)
DO.accept('control-g',func4)
DO.accept('escape',exit)
DO.accept('window-event',resetModButtons)

camera.setY(-5)
base.disableMouse()
run()
