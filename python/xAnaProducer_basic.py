import ROOT
import math

from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module


class xAnaProducer(Module):

    def __init__(self, isMC=True):
        self.isMC = isMC

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):

        self.out = wrappedOutputTree

        # Event branches
        self.out.branch("rho", "F")
        self.out.branch("rhoAll", "F")
        self.out.branch("event", "L")
        self.out.branch("run", "I")
        self.out.branch("lumis", "I")
        self.out.branch("isPVGood", "O")

        if self.isMC:
            self.out.branch("genWeight", "F")
            self.out.branch("puTrue", "F")

        # Muons
        self.out.branch("nMu", "I")
        self.out.branch("muPt", "F", lenVar="nMu")
        self.out.branch("muEta", "F", lenVar="nMu")
        self.out.branch("muPhi", "F", lenVar="nMu")
        self.out.branch("muEn", "F", lenVar="nMu")
        self.out.branch("muD0", "F", lenVar="nMu")
        self.out.branch("muDz", "F", lenVar="nMu")
        self.out.branch("muSIP", "F", lenVar="nMu")
        self.out.branch("muCharge", "I", lenVar="nMu")
        self.out.branch("muTrkLayers", "I", lenVar="nMu")
        self.out.branch("muStations", "I", lenVar="nMu")

        # Photons
        self.out.branch("nPho", "I")
        self.out.branch("phoCalibEt", "F", lenVar="nPho")
        self.out.branch("phoEta", "F", lenVar="nPho")
        self.out.branch("phoPhi", "F", lenVar="nPho")
        self.out.branch("phoSCEta", "F", lenVar="nPho")
        self.out.branch("phoIDMVA", "F", lenVar="nPho")
        self.out.branch("phoEleVeto", "I", lenVar="nPho")
        self.out.branch("phoHoverE", "F", lenVar="nPho")
        self.out.branch("phoCorrR9Full5x5", "F", lenVar="nPho")

        # Jets
        self.out.branch("nJet", "I")
        self.out.branch("jetPt", "F", lenVar="nJet")
        self.out.branch("jetEta", "F", lenVar="nJet")
        self.out.branch("jetPhi", "F", lenVar="nJet")

    def analyze(self, event):

        self.out.fillBranch("run", event.run)
        self.out.fillBranch("lumis", event.luminosityBlock)
        self.out.fillBranch("isPVGood", event.PV_npvsGood > 0)

        if self.isMC:
            self.out.fillBranch("genWeight", event.genWeight)
            self.out.fillBranch("puTrue", event.Pileup_nTrueInt)

        ########################
        # MUONS
        ########################

        nMu = event.nMuon

        muPt = []
        muEta = []
        muPhi = []
        muEn = []
        muD0 = []
        muDz = []
        muSIP = []
        muCharge = []
        muTrkLayers = []
        muStations = []

        for i in range(nMu):

            pt = event.Muon_pt[i]
            eta = event.Muon_eta[i]
            phi = event.Muon_phi[i]
            mass = event.Muon_mass[i]

            p4 = ROOT.TLorentzVector()
            p4.SetPtEtaPhiM(pt, eta, phi, mass)

            muPt.append(pt)
            muEta.append(eta)
            muPhi.append(phi)
            muEn.append(p4.E())
            muD0.append(event.Muon_dxy[i])
            muDz.append(event.Muon_dz[i])
            muSIP.append(event.Muon_sip3d[i])
            muCharge.append(event.Muon_charge[i])
            muTrkLayers.append(event.Muon_nTrackerLayers[i])
            muStations.append(event.Muon_nStations[i])

        self.out.fillBranch("nMu", nMu)
        self.out.fillBranch("muPt", muPt)
        self.out.fillBranch("muEta", muEta)
        self.out.fillBranch("muPhi", muPhi)
        self.out.fillBranch("muEn", muEn)
        self.out.fillBranch("muD0", muD0)
        self.out.fillBranch("muDz", muDz)
        self.out.fillBranch("muSIP", muSIP)
        self.out.fillBranch("muCharge", muCharge)
        self.out.fillBranch("muTrkLayers", muTrkLayers)
        self.out.fillBranch("muStations", muStations)

        ########################
        # PHOTONS
        ########################

        nPho = event.nPhoton

        phoCalibEt = []
        phoEta = []
        phoPhi = []
        phoSCEta = []
        phoIDMVA = []
        phoEleVeto = []
        phoHoverE = []
        phoR9 = []

        for i in range(nPho):

            phoCalibEt.append(event.Photon_pt[i])
            phoEta.append(event.Photon_eta[i])
            phoPhi.append(event.Photon_phi[i])

            sceta = event.Photon_eta[i] + event.Photon_deltaEtaSC[i]
            phoSCEta.append(sceta)

            phoIDMVA.append(event.Photon_mvaID[i])
            phoEleVeto.append(event.Photon_electronVeto[i])
            phoHoverE.append(event.Photon_hoe[i])
            phoR9.append(event.Photon_r9[i])

        self.out.fillBranch("nPho", nPho)
        self.out.fillBranch("phoCalibEt", phoCalibEt)
        self.out.fillBranch("phoEta", phoEta)
        self.out.fillBranch("phoPhi", phoPhi)
        self.out.fillBranch("phoSCEta", phoSCEta)
        self.out.fillBranch("phoIDMVA", phoIDMVA)
        self.out.fillBranch("phoEleVeto", phoEleVeto)
        self.out.fillBranch("phoHoverE", phoHoverE)
        self.out.fillBranch("phoCorrR9Full5x5", phoR9)

        ########################
        # JETS
        ########################

        nJet = event.nJet

        jetPt = []
        jetEta = []
        jetPhi = []

        for i in range(nJet):
            jetPt.append(event.Jet_pt[i])
            jetEta.append(event.Jet_eta[i])
            jetPhi.append(event.Jet_phi[i])

        self.out.fillBranch("nJet", nJet)
        self.out.fillBranch("jetPt", jetPt)
        self.out.fillBranch("jetEta", jetEta)
        self.out.fillBranch("jetPhi", jetPhi)

        return True        
