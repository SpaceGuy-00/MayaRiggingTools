import maya.cmds as mc
import maya.mel as mel
from maya.OpenMaya import MVector
import maya.OpenMayaUI as omui
from PySide2.QtWidgets import QVBoxLayout, QWidget, QPushButton, QMainWindow, QHBoxLayout, QGridLayout, QLineEdit, QLabel, QSlider
from PySide2.QtCore import Qt
from shiboken2 import wrapInstance

class LimbRiggerWidget(QWidget):
    def __init__(self):
        mainWindow: QMainWindow = LimbRiggerWidget.GetMayaMainWindow()

        for existing in mainWindow.findChildren(QWidget, LimbRiggerWidget.GetWindowUniqueId()):
            existing.deleteLater()
        super().__init__(parent=mainWindow)

        self.setWindowTitle("Limb Rigging Tool")
        self.setWindowFlags(Qt.Window)
        self.setObjectName(LimbRiggerWidget.GetWindowUniqueId())
        self.ControllerSize = 15


        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        hintLabel = QLabel("Please Select the Root, Middle, and End Joint of your Limb:")
        self.masterLayout.addWidget(hintLabel)

        controllerSizeCtrlLayout =QHBoxLayout()
        self.masterLayout.addLayout(controllerSizeCtrlLayout)

        controllerSizeCtrlLayout.addWidget(QLabel("Controller Size: "))
        controllerSizeSlider = QSlider()
        controllerSizeSlider.setValue(self.ControllerSize)
        controllerSizeSlider.setMinimum(1)
        controllerSizeSlider.setMaximum(30)
        controllerSizeSlider.setOrientation(Qt.Horizontal)
        controllerSizeCtrlLayout.addWidget(controllerSizeSlider)
        self.sizeDisplayLabel = QLabel(str(self.ControllerSize))
        controllerSizeSlider.valueChanged.connect(self.ControllerSizeChanged)
        controllerSizeCtrlLayout.addWidget(self.sizeDisplayLabel)

        rigLimbBtn = QPushButton("Rig the Limb")
        rigLimbBtn.clicked.connect(self.RigTheLimb)
        self.masterLayout.addWidget(rigLimbBtn)

    def RigTheLimb(self):
        selection = mc.ls(sl=True)

        rootJnt = selection[0]
        midJnt = selection[1]
        endJnt = selection[2]

        rootFkCtrl, rootFKCtrlGrp = self.CreateFKForJnt(rootJnt)
        midFkCtrl, midFKCtrlGrp = self.CreateFKForJnt(midJnt)
        endFKCtrl, endFKCtrlGRP = self.CreateFKForJnt(endJnt)

        mc.parent (midFkCtrl, rootFkCtrl)
        mc.parent(endFKCtrl, midFkCtrl)

        ikEndCtrlName, ikEndCtrlGrpName, midIKCtrlName, midIKCtrlGrpName, ikHandelName = self.CreateIKControl(rootJnt, midJnt, endJnt)

        ikfkBlendCtrlName = "ac_ikfk_blend_" + rootJnt
        mel.eval(f"curve -d 1 -n {ikfkBlendCtrlName} -p 0.0391662 10.062701 0 -p -1 10.062701 0 -p -1 9 0 -p -1 9 0 -p -2 9 0 -p -2 8 0 -p -1 8 0 -p -1 7 0 -p 0 7 0 -p 0 8 0 -p 1 8 0 -p 1 9 0 -p 0 9 0 -p 0 10 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 ;")
        ikfkBlendCtrlGrpName = ikfkBlendCtrlName + "_grp"
        mc.group(ikfkBlendCtrlName, n = ikfkBlendCtrlGrpName)

        rootJntPosVals = mc.xform(rootJnt, t=True, q=True, ws=True)
        rootJntPos = MVector(rootJntPosVals[0], rootJntPosVals[1], rootJntPosVals[2])
        ikfkBlendCtrlPos = rootJntPos + MVector(rootJntPos.x, 0,0)
        mc.move(ikfkBlendCtrlPos[0], ikfkBlendCtrlPos[1], ikfkBlendCtrlPos [2], ikfkBlendCtrlGrpName)

        ikfkBlendAttrName ="ikfk_blend"
        mc.addAttr(ikfkBlendCtrlName, Ln=ikfkBlendAttrName, k=True, min = 0, max =1)

        mc.expression(s=f"{rootFkCtrl}.v=1-{ikfkBlendCtrlName}.{ikfkBlendAttrName};")
        mc.expression(s=f"{ikEndCtrlGrpName}.v={ikfkBlendCtrlName}.{ikfkBlendAttrName};")
        mc.expression(s=f"{midIKCtrlGrpName}.v={ikfkBlendCtrlName}.{ikfkBlendAttrName};")
        mc.expression(s=f"{ikHandelName}.ikBlend={ikfkBlendCtrlName}.{ikfkBlendAttrName};")

        endJntOrientConstraint = mc.listConnections(endJnt, s=True, t="orientConstraint")[0]
        mc.expression(s=f"{endJntOrientConstraint}.{endFKCtrl}w0 =1-{ikfkBlendCtrlName}.{ikfkBlendAttrName};")
        mc.expression(s=f"{endJntOrientConstraint}.{ikEndCtrlGrpName}w1={ikfkBlendCtrlName}.{ikfkBlendAttrName};")

        topGrpName =f"{rootJnt}_rig_grp"
        mc.group([rootFKCtrlGrp, ikEndCtrlGrpName, midIKCtrlGrpName, ikfkBlendCtrlGrpName], n= topGrpName)


    def CreateFKForJnt (self, jnt):
        fkCtrlName = "ac_fk_" + jnt
        fkCtrlGrpName = fkCtrlName + "_grp"
        mc.circle(n=fkCtrlName, r=self.ControllerSize, nr=(1,0,0))
        mc.group(fkCtrlName, n = fkCtrlName)
        mc.matchTransform(fkCtrlName, jnt)
        mc.orientConstraint(fkCtrlName, jnt)
        return fkCtrlName, fkCtrlGrpName
       
    def CreateIKControl(self, rootJnt, midJnt, endJnt):
        ikEndCtrlName = "ac_ik_" + endJnt
        mel.eval(f"curve -d 1 -n {ikEndCtrlName} -d 1 -p -0.5 0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 0.5 0.5 -p -0.5 0.5 0.5 -p -0.5 0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 0.5 0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 0.5 0.5 -p 0.5 -0.5 0.5 -p -0.5 -0.5 0.5 -p -0.5 -0.5 -0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 -k 18 -k 19 -k 20 -k 21 -k 22 -k 23 -k 24 ; ")
        mc.scale(self.ControllerSize, self.ControllerSize, self.ControllerSize, ikEndCtrlName, r=True)
        mc.makeIdentity(ikEndCtrlName, apply=True) #freeze transformation
        ikEndCtrlGrpName = ikEndCtrlName + "_grp"
        mc.group(ikEndCtrlName, n = ikEndCtrlGrpName)
        mc.matchTransform(ikEndCtrlGrpName, endJnt)
        mc.orientConstraint(ikEndCtrlGrpName, endJnt)

        #ik handel
        ikHandelName = "ikHandle_" + endJnt
        mc.ikHandle(n=ikHandelName, sj=rootJnt, ee=endJnt, sol="ikRPsolver")


        rootJntPosVals = mc.xform(rootJnt, q=True, t=True, ws=True) #getting the world space (ws=True) of the Jnt, as a list of 3 values
        rootJntPos = MVector(rootJntPosVals[0], rootJntPosVals [1], rootJntPosVals [2])

        endJntPosVals = mc.xform(endJnt, q=True, t=True, ws=True)
        endJntPos =MVector (endJntPosVals[0], endJntPosVals [1], endJntPosVals [2])

        poleVectorVals = mc.getAttr(ikHandelName + ".poleVector")[0]
        poleVector = MVector(poleVectorVals[0], poleVectorVals [1], poleVectorVals [2])
        poleVector.normalize()

        vectorToEnd = endJntPos - rootJntPos
        limbDirOffset = vectorToEnd/2

        poleVectorDirOffset = poleVector * limbDirOffset.length()
        midIKCtrlPos : MVector = rootJntPos + limbDirOffset + poleVectorDirOffset

        midIKCtrlName = "ac_ik" + midJnt
        mc.spaceLocator(n=midIKCtrlName)

        midIKCtrlGrpName = midIKCtrlName + "_grp"
        mc.group(midIKCtrlName, n = midIKCtrlGrpName)
        mc.move(midIKCtrlPos.x, midIKCtrlPos.y, midIKCtrlPos.z, midIKCtrlGrpName)

        mc.parent(ikHandelName, ikEndCtrlName)
        mc.poleVectorConstraint(midIKCtrlName, ikHandelName)
        mc.setAttr(ikHandelName+".v",0)
        return ikEndCtrlName, ikEndCtrlGrpName, midIKCtrlName, midIKCtrlGrpName, ikHandelName

            



    def ControllerSizeChanged(self, sliderVal):
        self.sizeDisplayLabel.setText(str(sliderVal))
        self.ControllerSize = sliderVal

    @staticmethod
    def GetMayaMainWindow():
        mainWindow = omui.MQtUtil.mainWindow()
        return wrapInstance(int(mainWindow), QMainWindow)
    
    @staticmethod
    def GetWindowUniqueId():
        return "8fd40348d74f7b21a153ce39653a7d28"
def Run():
    global LimbRiggerWidget
    LimbRigger = LimbRiggerWidget()
    LimbRiggerWidget().show()

Run()