"""
Created on Wed Jan 31 13:20:49 2018

@author: Joel F. Andrews
"""

from ij import ImagePlus,ImageListener,WindowManager, IJ
from ij.gui import Roi, Overlay, WaitForUserDialog
from ij.plugin.frame import RoiManager, ContrastAdjuster
from ij.plugin import Concatenator
from ij.measure import ResultsTable
from java.awt import FileDialog, Color, TextArea, Rectangle, Dimension
from ij.io import FileSaver, Opener
import os
from javax.swing import JFileChooser, JOptionPane
#from javax.awt import JComboBox
from os.path import join
from ij import ImagePlus,ImageListener,WindowManager, IJ
from java.awt.event import MouseAdapter,KeyAdapter
import codecs



def IF_Analysis():
	names = JOptionPane()
	
	if filecount==1:	
		for c in range(1,channels+1):
			img.setC(c)
			namelist.append(names.showInputDialog('Name of Channel' + str(c) + '?'))
	sel = JOptionPane.showInputDialog(None, "Select Primary Channel", "Selection", JOptionPane.QUESTION_MESSAGE,None, namelist,namelist[1])
	img.setC(namelist.index(sel)+1)

	manager = RoiManager.getRoiManager()
	manager.reset()

	
	settings = data[1].split('\t')
	rois = int(settings[1])

	roiSize = data[3].split('\t')
	roiWidth = int(roiSize[5])-int(roiSize[3])+1
	roiHeight = int(roiSize[6]) -int(roiSize[4])+1
	xy=[]
	incl = []
	stim = []
	def zoom():
		z = manager.getSelectedIndex()
		
		x = int(manager.getRoi(manager.getSelectedIndex()).getXBase())
		y = int(manager.getRoi(manager.getSelectedIndex()).getYBase())
		if x-70<0:
			newx = 0
		else:
			newx = x
		if y-70<0:
			newy = 0
		else:
			newy = y
		rect = Rectangle(newx,newy,150,150)
		img.getCanvas().setSourceRect(rect)
		

	def importRois():
		manager.reset()

		for r in range(int(rois)):

			datum = data[r+3].split('\t')
			roi = "Roi" + str(r)
			x = float(datum[3])
			y = float(datum[4])
			
			width = float(datum[5])-float(datum[3])+1
			height = float(datum[6])-float(datum[4])+1

			roi = Roi(float(datum[3]), float(datum[4]),width + int(factor),height + int(factor))
			roi.setPosition(0,0,0)
			roi.setName('Roi_' + str(r+1))
			manager.addRoi(roi)
			stim.append(roi)



	def controlRois():
		manager.runCommand("Delete")
		IJ.run("Set Measurements...", "mean integrated redirect=None decimal=3")
		IJ.run("Duplicate...",'duplicate channels='+str(1))
		ch1 = IJ.getImage()
		
		manager.runCommand("Show All without Labels")
		

		IJ.run("Gaussian Blur...", "sigma=3")
		

		IJ.run("Auto Threshold", "method=Otsu white")

		IJ.run("Watershed")
		

		watershed = IJ.getImage()
		IJ.run("Set Measurements...", "area shape redirect=None decimal=3")

		IJ.run("Analyze Particles...", "size=25-Infinity display clear add")
		

		nuclei = manager.getRoisAsArray()
		count = manager.getCount()
		excl = []
		for c in range(count):

			manager.runCommand("Deselect")
			manager.select(c)

			for z in range(len(xy)):
				
				if manager.getRoi(manager.getSelectedIndex()).contains(int(xy[z][0]),int(xy[z][1])) ==True:
					included = True
					print("xy" + str(z))
					manager.getRoi(manager.getSelectedIndex()).setName('Roi_'+str(z+1)+'_Ref')
					incl.append(manager.getRoi(manager.getSelectedIndex()))
					break
				else:
					included = False
			if included == True:
				pass
			else:
				excl.append(c)
		
		manager.runCommand("Select All")
		manager.runCommand("Deselect")
		
		manager.setSelectedIndexes(excl)
		manager.runCommand("Delete")

		inclNuclei = manager.getRoisAsArray()

		manager.runCommand("Delete")
		manager.reset()
		
		watershed = IJ.getImage()
		watershed.changes = False
		watershed.close()

		return inclNuclei


		

	pane = JOptionPane()

	factor=0
	option = pane.showConfirmDialog(None,'Resize Rois?')

	if option == 0:
		factor = pane.showInputDialog('Current ROI Size = ' + str(roiWidth) + ' x ' + str(roiHeight)  + '\n#Pixels to add to Roi?')


	
	importRois()


	Prekls = img.getCanvas().getKeyListeners()
	map(img.getCanvas().removeKeyListener,Prekls)

	class kl_Lock_Roi(KeyAdapter):
		def keyTyped(self,event):
			k = event.getKeyChar()
			if(k=="\t"):
				event.consume()
				manager.runCommand(img,"Update")
				img.getCanvas().unzoom()
				manager.select(manager.getSelectedIndex()+1)
				zoom()
	kl = kl_Lock_Roi()
	img.getCanvas().addKeyListener(kl)


	manager.runCommand("Show All")
	manager.select(0)
	zoom()
	d = WaitForUserDialog('Place ROIs\nPress Tab to Select Next ROI')
	d.show()

	stimRois = manager.getRoisAsArray()
	stimCount = manager.getCount()
	manager.runCommand("Select All")
	manager.runCommand("Deselect")
	for c in range(stimCount):
		xy.append([])
		manager.select(c)
		xy[-1].append(manager.getRoi(manager.getSelectedIndex()).getXBase())
		xy[-1].append(manager.getRoi(manager.getSelectedIndex()).getYBase())

	control = pane.showConfirmDialog(None,"Add Control Rois?")

	if control ==0:
		nuc = controlRois()
		for s in stimRois:
			manager.addRoi(s)
		for c in range(stimCount):
			manager.select(c)
			name = manager.getRoi(manager.getSelectedIndex()).getName()
			print(name)
			for i in range(len(incl)):
				refname = incl[i].getName()

				if refname[:refname.rfind('_')] == name:
					manager.addRoi(incl[i])
					print("Roi" + str(c+1) + " with " + refname)
				else:
					pass

	else:
		for s in stimRois:
			manager.addRoi(s)


	roiList=manager.getRoisAsArray()
	
	output= ''
	results =[]
	table = ResultsTable.getResultsTable()
	manager.runCommand("Select All")
	manager.runCommand("Deselect")
	manager.runCommand("Delete")
	
	IJ.run("Select None")
	output = 'ROI ID'
	for n in namelist:
		output = output + '\t' + n + ' Mean Intensity'
	output = output + '\n'
	intensity = []
	IJ.run("Clear Results")
	manager.reset()
	IJ.run("Set Measurements...", "mean integrated redirect=None decimal=3");
	for c in range(1,channels+1):
		
		manager.reset()
		
		intensity.append([])
		IJ.run("Clear Results")
		table = ResultsTable.getResultsTable()
		ch = IJ.run("Duplicate...",'duplicate channels='+str(c))
		for roi in roiList:
			
			manager.addRoi(roi)
		manager.runCommand("Show All")
		manager.runCommand("Select All")
		
		manager.runCommand("Measure")
		for r in range(table.size()):
			results.append(table.getRowAsString(r))
			intensity[-1].append(table.getRowAsString(r).split('\t')[1])
		
		IJ.run("Clear Results")
		
		manager.runCommand("Delete")
		
		IJ.getImage().close()
	for roi in roiList:
		manager.addRoi(roi)
	manager.runCommand("Save", nd2[:-4] + '_' + 'XY' + "_RoiSet.zip");
	print(len(intensity))
	print([len(i) for i in intensity])

	for i in range(len(intensity[0])):
		output = output + str(i+1)
		for c in range(len(intensity)):
			output = output + '\t' + intensity[c][i]
		output = output + '\n'



	
	fullpath = info.directory + info.fileName
	print(fullpath)
	
	analysisTxt2 = fullpath[:-4] + '_ij_Data.txt'
	with codecs.open(analysisTxt2,'w', encoding="utf-16-le") as myFile:

		myFile.write(output)
		myFile.close()
	
def Timelapse_Analysis():
	dataTypes = 3
	anchor = []
	anchor.append([])
	skip = 8
	numAnchors = frames/skip
	tracks = []
	tracks.append([])
	names = JOptionPane()
	
	if filecount==1:
		for c in range(1,channels+1):
			img.setC(c)
			namelist.append(names.showInputDialog('Name of Channel' + str(c) + '?'))
	sel = JOptionPane.showInputDialog(None, "Select Primary Channel", "Selection", JOptionPane.QUESTION_MESSAGE,None, namelist,namelist[1])
	img.setC(namelist.index(sel)+1)

	manager = RoiManager.getRoiManager()
	manager.reset()

	settings = data[1].split('\t')
	rois = int(settings[1])
	interval = float(settings[3])
	offset = data[2+rois].split('\t')
	maxoffset = float(offset[2])
	roiSize = data[3].split('\t')
	roiWidth = int(roiSize[5])-int(roiSize[3])+1
	roiHeight = int(roiSize[6]) -int(roiSize[4])+1


	time = []
	time.append(0)
	time.append(200)
	for f in range(1,frames-1):
		time.append(1000*(interval*f))

	for f in range(frames):
		tracks.append([])
		for r in range(2*rois):
			tracks[f].append([])
			for d in range(dataTypes):
				tracks[f][r].append([])
				tracks[f][r][d]= None

	def importRois():
		manager.reset()

		for r in range(int(rois)):
			datum = data[r+3].split('\t')
			roi = "Roi" + str(r)
			x = float(datum[3])
			y = float(datum[4])
			width = float(datum[5])-float(datum[3])+1
			height = float(datum[6])-float(datum[4])+1
			tracks[0][r][0] = x
			tracks[0][r][1] = y
			tracks[0][r][2] = 1
			for f in range(1,frames):
				tracks[f][r][0] = x
				tracks[f][r][1] = y
				tracks[f][r][2] = 0
			roi = Roi(float(datum[3]), float(datum[4]),width + int(factor),height + int(factor))
			roi.setPosition(0,0,0)

			manager.addRoi(roi)

	def controlRois():
		for r in range(rois):
			manager.select(r)
			x = manager.getRoi(manager.getSelectedIndex()).getXBase()
			y = manager.getRoi(manager.getSelectedIndex()).getYBase()
			height = manager.getRoi(manager.getSelectedIndex()).getFloatHeight()
			width = manager.getRoi(manager.getSelectedIndex()).getFloatWidth()
			roi = "Roi" + str(r+rois)
			tracks[0][r+rois][0] = x - 15
			tracks[0][r+rois][1] = y - 15
			tracks[0][r+rois][2] = 1
			for f in range(1,frames):
				tracks[f][r+rois][0] = x - 15
				tracks[f][r+rois][1] = y - 15
				tracks[f][r+rois][2] = 0
			roi = Roi(x-15,y-15,width,height)
			roi.setPosition(0,0,0)
			manager.addRoi(roi)


	pane = JOptionPane()
	factor = 0
	importRois()
	
	control = pane.showConfirmDialog(None,"Add Control Rois?")

	if control ==0:
		controlRois()
	else: pass

	option = pane.showConfirmDialog(None,'Resize Rois?')

	if option == 0:
		factor = pane.showInputDialog('Current ROI Size = ' + str(roiWidth) + ' x ' + str(roiHeight)  + '\n#Pixels to add to Roi?')
		importRois()
		if control ==0:
			controlRois()


	else: pass


	manager.runCommand("Show All")




	def addAnchor():
		x = manager.getRoi(manager.getSelectedIndex()).getXBase()
		y = manager.getRoi(manager.getSelectedIndex()).getYBase()
		tracks[img.getT()-1][manager.getSelectedIndex()][0] = x
		tracks[img.getT()-1][manager.getSelectedIndex()][1] = y
		tracks[img.getT()-1][manager.getSelectedIndex()][2] = 1


	def zoom():

		z = manager.getSelectedIndex()
		
		x = int(manager.getRoi(manager.getSelectedIndex()).getXBase())
		y = int(manager.getRoi(manager.getSelectedIndex()).getYBase())
		rect = Rectangle(x-70,y-70,150,150)
		img.getCanvas().setSourceRect(rect)
		

	def fillBackDamage():
		for r in range(rois):
			anchor1X = tracks[0][r][0]
			anchor1Y = tracks[0][r][1]
			count = 1
			for f in range(1,frames):
				if (tracks[f][r][2] == 0):
					count = count + 1

					continue
				if (tracks[f][r][2] == 1):
					anchor2X = tracks[f][r][0]
					anchor2Y = tracks[f][r][1]
					diffX = anchor2X - anchor1X
					diffY =  anchor2Y - anchor1Y
					for c in range(count+1):
						tracks[f-c][r][0] = anchor1X + (count-c)*(diffX/count)
						tracks[f-c][r][1] = anchor1Y + (count-c)*(diffY/count)
					count = 1
					anchor1X = tracks[f][r][0]
					anchor1Y = tracks[f][r][1]
				continue
	def fillBackControls():
		for r in range(rois,2*rois):
			anchor1X = tracks[0][r][0]
			anchor1Y = tracks[0][r][1]
			count = 1
			for f in range(1,frames):
				if (tracks[f][r][2] == 0):
					count = count + 1

					continue
				if (tracks[f][r][2] == 1):
					anchor2X = tracks[f][r][0]
					anchor2Y = tracks[f][r][1]
					diffX = anchor2X - anchor1X
					diffY =  anchor2Y - anchor1Y
					for c in range(count+1):
						tracks[f-c][r][0] = anchor1X + (count-c)*(diffX/count)
						tracks[f-c][r][1] = anchor1Y + (count-c)*(diffY/count)
					count = 1
					anchor1X = tracks[f][r][0]
					anchor1Y = tracks[f][r][1]
				continue

	def advance():
		t = img.getT()
		if (t<numAnchors):
			img.setT(1)
			addAnchor()
		else: pass
		img.setT(t+numAnchors)
		if (t+numAnchors >=frames):
			addAnchor()
			
			img.setT(1)

			manager.getRoi(manager.getSelectedIndex()).setStrokeColor(yellow);
			manager.select(manager.getSelectedIndex()+1)
			manager.getRoi(manager.getSelectedIndex()).setStrokeColor(white);
			if manager.getSelectedIndex()>=rois:
				fillBackDamage()
			zoom()
		else:
			pass

	class kl_anchor_advance(KeyAdapter):
		def keyTyped(self,event):
			k = event.getKeyChar()
			if(k=="\t"):
				event.consume()
				manager.runCommand(img,"Update")
				addAnchor()
				x = manager.getRoi(manager.getSelectedIndex()).getXBase()
				y = manager.getRoi(manager.getSelectedIndex()).getYBase()


				advance()


			if(k=="f"):
				img.setT(1)
				manager.runCommand(img,"Update")
				addAnchor()
				x = manager.getRoi(manager.getSelectedIndex()).getXBase()
				y = manager.getRoi(manager.getSelectedIndex()).getYBase()

				pass

	Prekls = img.getCanvas().getKeyListeners()
	map(img.getCanvas().removeKeyListener,Prekls)

	kl = kl_anchor_advance()
	img.setT(1)
	img.getCanvas().addKeyListener(kl)

	manager.runCommand(img,"Show All with labels");
	manager.select(0)

	white = Color(255,255,255)
	yellow = Color(255,255,0)
	manager.getRoi(manager.getSelectedIndex()).setStrokeColor(white);
	zoom()
	class IL(ImageListener):
		def __init__(self):
			a = WindowManager.getCurrentImage()
			a.addImageListener(self)

		def imageUpdated(self,a):
			for r in range(2*rois):
				R = manager.getRoi(r)

				frame = a.getT()

				if (R.getXBase() != tracks[frame-1][r][0]) or (R.getYBase() != tracks[frame-1][r][1]):

					R.setLocation(tracks[frame-1][r][0],tracks[frame-1][r][1])

					manager.runCommand(img,"Update")
				else:
					pass



		def imageClosed(self,a):
			a.removeImageListener(self)
			manager.reset()
			IJ.log("closed")
	il = IL()
	d = WaitForUserDialog('Move Roi to Correct Location\nPress F to Place First Frame\nPress Tab to Advance')
	d.show()

	fillBackControls()
	kls = img.getCanvas().getKeyListeners()
	map(img.getCanvas().removeKeyListener,kls)

	class kl_anchor(KeyAdapter):
		def keyTyped(self,event):
			k = event.getKeyChar()
			if(k=="\t"):
				manager.runCommand(img,"Update")
				addAnchor()

				fillBack()




	al = kl_anchor()
	img.getCanvas().addKeyListener(al)
	d = WaitForUserDialog('Adjust Rois as Necessary\nPress Tab to Lock Roi to Frame')
	d.show()

	img.getCanvas().removeKeyListener(al)

	output = 'ROI ID\tTime'
	for c in range(1,channels+1):
		output = output + '\t' + namelist[c-1] +' Mean Intensity'
	output = output + '\n'
	results = ResultsTable.getResultsTable()

	img.setT(1)

	for f in range(1,frames+1):
		img.setT(f)

		for r in range(2*rois):
			manager.getRoi(r).setPosition(0,0,0)


			manager.select(r)
			output = output + str(r+1) + '\t' + str(time[f-1])
			for c in range(1,channels+1):
				output = output + '\t'
				img.setC(c)
				manager.runCommand("Measure")
				
				value = results.getValueAsDouble(1,0)
				results.reset()
				output = output + str(value)
			output = output + '\n'
			manager.deselect()
	print(output)
	info = img.getOriginalFileInfo()
	fullpath = info.directory + info.fileName
	analysisTxt = fullpath[:-4] + '_ij_Data.txt'
	with codecs.open(analysisTxt,'w', encoding="utf-16-le") as myFile:

		myFile.write(output)
		myFile.close()

def Concat():
	for root, dirs, files in os.walk(path):
		for f in files:
			if '_Post.nd2' in f:
				post = f
				pre = join(root,f[:-8]+'Pre.nd2')
				try:
					img1 = opener.openUsingBioFormats(pre)
					img1.show()
				except:
					break
				post = join(root, post)
				img2 = opener.openUsingBioFormats(post)
				img2.show()
				img3 = Concatenator.run(img1,img2)
				img3.show()
				concat = post[:-8] + '.nd2'
				saver = FileSaver(img3)
				saver.saveAsTiff(concat)
				img3.close()
			else:
				pass



filecount = 0
chooser = JFileChooser()
chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)
chooser.showOpenDialog(None)
directory = chooser.getSelectedFile()
path = directory.getCanonicalPath()
opener = Opener()
namelist = []

for root, dirs, files in os.walk(path):
	for f in files:
		if '_Post' in f:
			pane = JOptionPane()
			ret = pane.showConfirmDialog(None,'Concatenate Files?')
			if (ret==0):
				Concat()
				break
			else: break
		else:
			pass


for root, dirs, files in os.walk(path):
	for f in files:

		if ('_Pre' not in f) and ('_Post' not in f):


			if '.nd2' in f or '.tif' in f:
				IJ.run("Brightness/Contrast...")

				filecount=filecount+1
				nd2 = join(root,f)
				print(nd2)
				img = opener.openUsingBioFormats(nd2)
				img.show()
				

				dim = img.getDimensions()
				[imgWidth,imgHeight,channels,z,frames] = dim
				info = img.getOriginalFileInfo()
				directory = info.directory
				info = img.getOriginalFileInfo()
				directory = info.directory
				if (z!=1):
					print('Z stack detected!')
					IJ.run("Z Project...", "projection=[Max Intensity]")
					maxIP = IJ.getImage()
					img.changes == False
					img.close()
					img = maxIP
					
				try:
					settingsName = info.fileName[:-4] + "_Settings.txt"
					fullpath = info.directory + settingsName
					with codecs.open(fullpath,'r', encoding="utf-16-le") as f:
						data = f.readlines()
				except:
					fd = FileDialog(IJ.getInstance(),"Select Settings File",FileDialog.LOAD)
					fd.setDirectory(info.directory)
					fd.show()
					file_name = fd.getFile()
					path = fd.getDirectory()
					fullpath = path + file_name
					with codecs.open(fullpath,'r', encoding="utf-16-le") as f:
						data = f.readlines()


				if frames ==1:
					IF_Analysis()
				else: Timelapse_Analysis()
				img.close()


