# **************************************************************************
# *
# * Authors: Alberto Garcia Mena   (alberto.garcia@cnb.csic.es)
# *          Daniel Marchan (da.marchan@cnb.csic.es)
# *
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

"""
This protocol connect with smartscope in streaming. Recives all information
from the API, collect it in Scipion objects and will be able to communicate
to Smartscope to take decission about the acquisition
"""
from pyworkflow.utils import Message
from pyworkflow import BETA, UPDATED, NEW, PROD
from pwem.protocols.protocol_import.base import ProtImport
from pyworkflow.protocol import ProtStreamingBase
import pyworkflow.utils as pwutils
from smartscope import Plugin
from pyworkflow.object import Set
from ..objects.data import Hole

from pyworkflow.protocol import params, STEPS_PARALLEL
from ..objects.dataCollection import *
import time
from ..constants import *


class smartscopeFeedbackFilter(ProtImport, ProtStreamingBase):
	"""
	This protocol will calculate which are the best holes of the session based
	on the good particles of each hole. After knowing the good holes, will
	sort the queue of hole acquisition that Smartscope uses.
	"""
	_label = 'Feedback filter'
	_devStatus = BETA
	_possibleOutputs = {'SetOfHolesFiltered': SetOfHoles,
	                    'SeOfHolesFilteredOut': SetOfHoles}
	
	def __init__(self, **args):
		ProtImport.__init__(self, **args)
		self.stepsExecutionMode = STEPS_PARALLEL
		
		self.token = Plugin.getVar(SMARTSCOPE_TOKEN)
		self.endpoint = Plugin.getVar(SMARTSCOPE_LOCALHOST)
		self.dataPath = Plugin.getVar(SMARTSCOPE_DATA_SESSION_PATH)
		
		self.pyClient = MainPyClient(self.token, self.endpoint)
		self.connectionClient = dataCollection(self.pyClient)
		self.countStreamingSteps = 0
	
	def _defineParams(self, form):
		""" Define the input parameters that will be used.
		Params:
			form: this is the form to be populated with sections and params.
		"""
		# You need a params to belong to a section:
		form.addSection(label=Message.LABEL_INPUT)
		form.addParam('inputHoles', params.PointerParam,
		              pointerClass='SetOfHoles',
		              important=True, allowsNull=False,
		              label='Input holes from Smartscope',
		              help='Select a set of holes from Smartscope connection protocol.')
		form.addParam('inputMovies', params.PointerParam,
		              pointerClass='SetOfMoviesSS',
		              important=True, allowsNull=False,
		              label='Input movies from Smartscope',
		              help='Select a set of movies from Smartscope connection protocol.')
		# form.addParam('inputMicrographs', params.PointerParam, pointerClass='SetOfMicrographs',
		#               important=True, allowsNull=False,
		#               label='Input micrographs before filters',
		#               help='Select a set of holes from Smartscope connection protocol.')
		form.addParam('filteredMics', params.PointerParam,
		              pointerClass='SetOfMicrographs',
		              important=True, allowsNull=False,
		              label='Filtered micrographs',
		              help='Select a set of micrographs filtered by any protocol.')
		form.addParam('triggerMicrograph', params.IntParam, default=100,
		              label="Micrographs to launch the protocol",
		              help='Number of micrographs filtered to launch the statistics')
		form.addParam('binsHist', params.IntParam, default=50,
		              expertLevel=params.LEVEL_ADVANCED,
		              label="Number of bins of the Intensity histogram",
		              help='')
		form.addSection('Streaming')
		
		form.addParam('refreshTime', params.IntParam, default=120,
		              label="Time to refresh data collected (secs)")
		
		form.addParallelSection(threads=3, mpi=1)
	
	def _initialize(self):
		self.movies = self.inputMovies.get()
		self.holes = self.inputHoles.get()
		self.zeroTime = time.time()
		self.finish = False
	
	def stepsGeneratorStep(self):
		"""
		This step should be implemented by any streaming protocol.
		It should check its input and when ready conditions are met
		call the self._insertFunctionStep method.
		"""
		self._initialize()
		
		while not self.finish:
			rTime = time.time() - self.zeroTime
			if rTime >= self.refreshTime.get():
				self.zeroTime = time.time()
				self.info('len filteredMics: {}'.format(
					len(self.filteredMics.get())))
				if len(self.filteredMics.get()) >= self.triggerMicrograph.get():
					self.info('In progres...')
					self.countStreamingSteps += 1
					
					self.fMics = self.filteredMics.get()
					self.collectSetOfHolesFiltered()
					self.statistics()
					self.postingBack2Smartscope()
					self.createSetOfFilteredHoles()
					if not self.fMics.isStreamOpen():
						self.info(
							'Not more micrographs are expected, set closed')
						self.finish = True
				else:
					self.info('Waiting enought micrographs to launch protocol.'
					          ' triggerMicrograph: {}, micrographsFiltered: {}'.format(
						self.triggerMicrograph.get(),
						len(self.filteredMics.get())))
	
	def collectSetOfHolesFiltered(self):
		self.info('In collect')
		self.holesFiltered = []
		dictMovies = {}
		for m in self.movies:
			dictMovies[m.getMicName()] = m.clone()
		for mic in self.fMics:
			H_ID = dictMovies[mic.getMicName()].getHoleId()
			self.holesFiltered.append(H_ID)
		# self.info('hole from mic on holesFiltered')
		# self.info(self.holesFiltered)
	
	def statistics(self):
		self.info('statistics')
		import numpy as np
		listHoles = []
		listFilteredHoles = []
		for h in self.holes:
			listHoles.append(h.getSelectorValue())
			if h.getHoleId() in self.holesFiltered:
				listFilteredHoles.append(h.getSelectorValue())
		arrayHoles = np.array(listHoles)
		arrayFilteredHoles = np.array(listFilteredHoles)
		# Calcular los histogramas de ambas series
		minIntensity = min(listHoles)
		maxIntensity = max(listHoles)
		step = (maxIntensity - minIntensity) / self.binsHist.get()
		bins = np.linspace(minIntensity, maxIntensity,
		                   self.binsHist.get())  # Definir los l�mites de los bins para el histograma
		
		histTotal, rangeIntensity = np.histogram(arrayHoles, bins=bins)
		histFiltered, ranges = np.histogram(arrayFilteredHoles, bins=bins)
		self.debug('histTotal:{}\n \nhistFiltered: {}'.format(histTotal,
		                                                      histFiltered))
		# Asegurarse de que los histogramas tengan el mismo tama�o
		assert len(histTotal) == len(
			histFiltered), "Los histogramas no tienen la misma cantidad de bins"
		
		# Calcular el cociente de los histogramas
		self.histRatio = np.divide(histFiltered, histTotal,
		                           out=np.zeros_like(histFiltered,
		                                             dtype=float),
		                           where=histTotal != 0)
		self.histRatio[np.isinf(self.histRatio)] = 0.0
		self.histRatio[np.isnan(self.histRatio)] = 0.0
		
		self.debug('ranges: {}'.format(ranges))
		self.debug("histRatio: {}".format(self.histRatio))
		
		mu = np.sum(ranges[:-1] * self.histRatio) / np.sum(self.histRatio)
		sigma = np.sqrt(
			np.sum(self.histRatio * (ranges[:-1] - mu) ** 2) / np.sum(
				self.histRatio))
		self.minIntensity = int(mu - sigma)
		self.maxIntensity = int(mu + sigma + step)
		self.info('std_dev: {}\nmedian_value: {}'.format(sigma, mu))
		self.info(
			'minIntensity: {}\nmaxIntensity: {}'.format(self.minIntensity,
			                                            self.maxIntensity))
		# saving data to plot in extra folder
		rangeFile = self._getExtraPath(
			"rangeI-{}.txt".format(self.countStreamingSteps))
		np.savetxt(rangeFile, rangeIntensity[:-1].reshape(1, -1), fmt='%.8f',
		           delimiter=' ')
		histRatioFile = self._getExtraPath(
			"histRatio-{}.txt".format(self.countStreamingSteps))
		np.savetxt(histRatioFile, self.histRatio.reshape(1, -1), fmt='%.8f',
		           delimiter=' ')
		
		# SUMMARY INFO
		summaryF = self._getExtraPath("summary.txt")
		summaryF = open(summaryF, "w")
		summaryF.write(
			'Standard deviation: {}\nMedian value: {}\n'.format(int(sigma),
			                                                    int(mu)) +
			'Intensity range with holes to acquire: {} - {}'.format(
				self.minIntensity, self.maxIntensity))
		summaryF.close()
	
	def postingBack2Smartscope(self):
		# TODO post a setValueIntensity
		# TODO request regroup
		# TODO requeue
		# for h in self.holes:
		#     if self.minIntensity > h.getSelectorValue() or h.getSelectorValue() > self.maxIntensity and h.getStatus() != 'complete':
		#         self.pyClient.postParameterFromID('holes', h.getHoleId(), data={"selected": 'False'})
		pass
	
	def createSetOfFilteredHoles(self):
		SOH = SetOfHoles.create(outputPath=self._getPath())  # baseName
		SOHFO = SetOfHoles.create(outputPath=self._getPath(),
		                          prefix='FilteredOut')
		self.outputsToDefine = {'SetOfHolesFiltered': SOH,
		                        'SeOfHolesFilteredOut': SOHFO}
		self._defineOutputs(**self.outputsToDefine)
		for h in self.holes:
			if h.getHoleId() in self.holesFiltered:
				self.createOutputStep(SOH, h)
			else:
				self.createOutputStepFilteredOut(SOHFO, h)
	
	def createOutputStep(self, SOH, hole):
		SOH.copyInfo(self.holes)
		hole2Add_copy = Hole()
		hole2Add_copy.copy(hole, copyId=False)
		SOH.append(hole2Add_copy)
		if self.hasAttribute('SetOfHolesFiltered'):
			SOH.write()
			outputAttr = getattr(self, 'SetOfHolesFiltered')
			outputAttr.copy(SOH, copyId=False)
			self._store(outputAttr)
		# STORE SQLITE
		self._store(SOH)
	
	def createOutputStepFilteredOut(self, SOHFO, hole):
		SOHFO.copyInfo(self.holes)
		hole2Add_copy = Hole()
		hole2Add_copy.copy(hole, copyId=False)
		SOHFO.append(hole2Add_copy)
		if self.hasAttribute('SeOfHolesFilteredOut'):
			SOHFO.write()
			outputAttr = getattr(self, 'SeOfHolesFilteredOut')
			outputAttr.copy(SOHFO, copyId=False)
			self._store(outputAttr)
		# STORE SQLITE
		self._store(SOHFO)
	
	def checkSmartscopeConnection(self):
		response = self.pyClient.getDetailsFromParameter('users')
		return response
	
	def _summary(self):
		summary = []
		summaryF = self._getExtraPath("summary.txt")
		if not os.path.exists(summaryF):
			summary.append("No summary file yet.")
		else:
			summaryF = open(summaryF, "r")
			for line in summaryF.readlines():
				summary.append(line.rstrip())
			summaryF.close()
		return summary
	
	def _validate(self):
		errors = []
		# self._validateThreads(errors)
		
		if Plugin.getVar(
				SMARTSCOPE_TOKEN) == 'Read Smartscope documentation to get the token...':
			errors.append('SMARTSCOPE_TOKEN has not been configured, '
			              'please visit https://github.com/scipion-em/scipion-em-smartscope#configuration \n')
		if Plugin.getVar(SMARTSCOPE_LOCALHOST) == None:
			errors.append(
				'SMARTSCOPE_LOCALHOST has not been configured, please visit https://github.com/scipion-em/scipion-em-smartscope#configuration \n')
		if Plugin.getVar(
				SMARTSCOPE_DATA_SESSION_PATH) == 'Path assigned to the data in the Smartscope installation':
			errors.append(
				'SMARTSCOPE_DATA_SESSION_PATH has not been configured, '
				'please visit https://github.com/scipion-em/scipion-em-smartscope#configuration \n')
		
		response = self.checkSmartscopeConnection()
		try:
			response[0]['username']
		except Exception as e:
			try:
				errors.append('Error Smartscope connection:\n{}'.format(
					response['detail']))
			except Exception:
				errors.append(
					'Error Smartscope connection. Maybe launch Smartscope container...\n\n{}'.format(
						response))
		
		return errors