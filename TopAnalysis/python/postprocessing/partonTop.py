import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

import os
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

class PartonTop(Module, object):
    def __init__(self, *args, **kwargs):
        #super(PartonTop, self).__init__(*args, **kwargs)
        self.mode = kwargs.get("mode")
        self.algo = kwargs.get("algo")

        if "/PartonTop_cc.so" not in  ROOT.gSystem.GetLibraries():
            print "Load C++ PartonTop worker module"
            base = os.getenv("NANOAODTOOLS_BASE")
            if base:
                ROOT.gROOT.ProcessLine(".L %s/src/PartonTopCppWorker.cc+O" % base)
            else:
                base = "%s/src/TZWi/TopAnalysis"%os.getenv("CMSSW_BASE")
                ROOT.gSystem.Load("libPhysicsToolsNanoAODTools.so")
                ROOT.gSystem.Load("libTZWiTopAnalysis.so")
                ROOT.gROOT.ProcessLine(".L %s/interface/PartonTopCppWorker.h" % base)
        pass
    def beginJob(self):
        self.worker = ROOT.PartonTopCppWorker()
        pass
    def endJob(self):
        pass
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch("nParton", "i")
        self.out.branch("Parton_pt"    , "F", lenVar="nParton")
        self.out.branch("Parton_eta"   , "F", lenVar="nParton")
        self.out.branch("Parton_phi"   , "F", lenVar="nParton")
        self.out.branch("Parton_mass"  , "F", lenVar="nParton")
        self.out.branch("Parton_pdgId" , "I", lenVar="nParton")
        self.out.branch("Parton_mother", "I", lenVar="nParton")
        self.initReaders(inputTree)
        pass
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
    def initReaders(self,tree):

        objName = "GenPart"
        setattr(self, "n%s" % objName, tree.valueReader("n%s" % objName))
        for varName in ["pt", "eta", "phi", "mass", "pdgId", "status", "genPartIdxMother"]:
            setattr(self, "%s_%s" % (objName, varName), tree.arrayReader("%s_%s" % (objName, varName)))

        self.worker.setGenParticles(self.nGenPart,
                                    self.GenPart_pt, self.GenPart_eta, self.GenPart_phi, self.GenPart_mass,
                                    self.GenPart_pdgId, self.GenPart_status, self.GenPart_genPartIdxMother)
        self._ttreereaderversion = tree._ttreereaderversion

        pass
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        if event._tree._ttreereaderversion > self._ttreereaderversion:
            self.initReaders(event._tree)
        self.worker.genEvent()
        self.out.fillBranch("nParton", self.worker.get_n())
        for varName in ["pt", "eta", "phi", "mass", "pdgId", "mother"]:
            self.out.fillBranch("Parton_"+varName, getattr(self.worker, 'get_'+varName)())

        return True

partonTop = lambda : PartonTop()
