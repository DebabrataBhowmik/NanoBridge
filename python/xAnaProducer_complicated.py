import ROOT
import math

from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module


class xAnaProducer(Module):

    def __init__(self, year="2024", isMC=True):
        self.year = year
        self.isMC = isMC

    ############################################
    # BEGIN FILE
    ############################################
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):

        self.out = wrappedOutputTree

        ########################################
        # EVENT
        ########################################
        self.out.branch("rho", "F")
        self.out.branch("rhoAll", "F")

        self.out.branch("event", "L")
        self.out.branch("run", "I")
        self.out.branch("lumis", "I")

        self.out.branch("HLTEleMuX", "l")
        self.out.branch("isPVGood", "O")

        if self.isMC:
            self.out.branch("puTrue", "F")
            self.out.branch("genWeight", "F")

            self.out.branch("L1ECALPrefire", "F")
            self.out.branch("L1ECALPrefireUp", "F")
            self.out.branch("L1ECALPrefireDown", "F")

        ########################################
        # MUONS
        ########################################
        self.out.branch("nMu", "I")

        self.out.branch("muPt", "F", lenVar="nMu")
        self.out.branch("muEta", "F", lenVar="nMu")
        self.out.branch("muPhi", "F", lenVar="nMu")
        self.out.branch("muEn", "F", lenVar="nMu")

        self.out.branch("muD0", "F", lenVar="nMu")
        self.out.branch("muDz", "F", lenVar="nMu")

        self.out.branch("muBestTrkPtError", "F", lenVar="nMu")
        self.out.branch("muBestTrkPt", "F", lenVar="nMu")

        self.out.branch("muSIP", "F", lenVar="nMu")

        self.out.branch("muPFChIso03", "F", lenVar="nMu")
        self.out.branch("muPFPhoIso03", "F", lenVar="nMu")
        self.out.branch("muPFNeuIso03", "F", lenVar="nMu")
        self.out.branch("muPFPUIso03", "F", lenVar="nMu")

        self.out.branch("muCharge", "I", lenVar="nMu")
        self.out.branch("muType", "I", lenVar="nMu")

        self.out.branch("muTrkLayers", "I", lenVar="nMu")
        self.out.branch("muBestTrkType", "I", lenVar="nMu")

        self.out.branch("muPixelHits", "I", lenVar="nMu")
        self.out.branch("muStations", "I", lenVar="nMu")
        self.out.branch("muMatches", "I", lenVar="nMu")

        ########################################
        # PHOTONS
        ########################################
        self.out.branch("nPho", "I")

        self.out.branch("phoE", "F", lenVar="nPho")
        self.out.branch("phoEt", "F", lenVar="nPho")
        self.out.branch("phoCalibEt", "F", lenVar="nPho")

        self.out.branch("phoEta", "F", lenVar="nPho")
        self.out.branch("phoPhi", "F", lenVar="nPho")

        self.out.branch("phoSCEta", "F", lenVar="nPho")
        self.out.branch("phoSCPhi", "F", lenVar="nPho")

        self.out.branch("phoIDMVA", "F", lenVar="nPho")
        self.out.branch("phoEleVeto", "I", lenVar="nPho")

        self.out.branch("phoSCRawE", "F", lenVar="nPho")

        self.out.branch("phoSigmaIEtaIEtaFull5x5", "F", lenVar="nPho")
        self.out.branch("phoSCEtaWidth", "F", lenVar="nPho")
        self.out.branch("phoSCPhiWidth", "F", lenVar="nPho")

        self.out.branch("phoPFPhoIso", "F", lenVar="nPho")
        self.out.branch("phoPFChIso", "F", lenVar="nPho")
        self.out.branch("phoPFChWorstIso", "F", lenVar="nPho")

        self.out.branch("phoHoverE", "F", lenVar="nPho")

        self.out.branch("phoTrkIsoHollowConeDR03", "F", lenVar="nPho")

        self.out.branch("phoCorrR9Full5x5", "F", lenVar="nPho")
        self.out.branch("phoCorrHggIDMVA", "F", lenVar="nPho")

        ########################################
        # JETS
        ########################################
        self.out.branch("nJet", "I")

        self.out.branch("jetPt", "F", lenVar="nJet")
        self.out.branch("jetEta", "F", lenVar="nJet")
        self.out.branch("jetPhi", "F", lenVar="nJet")
        self.out.branch("jetEn", "F", lenVar="nJet")

        self.out.branch("jetNHF", "F", lenVar="nJet")
        self.out.branch("jetNEF", "F", lenVar="nJet")

        self.out.branch("jetID", "I", lenVar="nJet")

        self.out.branch("jetCHF", "F", lenVar="nJet")
        self.out.branch("jetCEF", "F", lenVar="nJet")
        self.out.branch("jetMUF", "F", lenVar="nJet")

        self.out.branch("jetNCH", "I", lenVar="nJet")
        self.out.branch("jetNNP", "I", lenVar="nJet")

        ########################################
        # GEN
        ########################################
        if self.isMC:

            self.out.branch("nMC", "I")

            self.out.branch("mcPID", "I", lenVar="nMC")
            self.out.branch("mcMomPID", "I", lenVar="nMC")
            self.out.branch("mcGMomPID", "I", lenVar="nMC")

            self.out.branch("mcPt", "F", lenVar="nMC")
            self.out.branch("mcEta", "F", lenVar="nMC")
            self.out.branch("mcPhi", "F", lenVar="nMC")
            self.out.branch("mcMass", "F", lenVar="nMC")

            self.out.branch("mcStatusFlag", "i", lenVar="nMC")

    ############################################
    # ANALYZE
    ############################################
    def analyze(self, event):

        ########################################
        # EVENT
        ########################################

        rho = event.Rho_fixedGridRhoFastjetAll

        self.out.fillBranch("rho", rho)
        self.out.fillBranch("rhoAll", rho)

        self.out.fillBranch("event", event.event)
        self.out.fillBranch("run", event.run)
        self.out.fillBranch("lumis", event.luminosityBlock)

        isPVGood = event.PV_npvsGood > 0
        self.out.fillBranch("isPVGood", isPVGood)

        ########################################
        # TRIGGER BITMAP
        ########################################

        HLTEleMuX = 0

        ########################################
        # BIT 8
        ########################################
        passMuPho = (
            getattr(event, "HLT_Mu17_Photon30_IsoCaloId", False)
            or getattr(event, "HLT_Mu17_Photon30_CaloIdL_L1ISO", False)
        )

        if passMuPho:
            HLTEleMuX |= (1 << 8)

        ########################################
        # BIT 19
        ########################################
        passSingleMu = (
            getattr(event, "HLT_IsoMu24", False)
            or getattr(event, "HLT_IsoMu27", False)
        )

        if passSingleMu:
            HLTEleMuX |= (1 << 19)

        self.out.fillBranch("HLTEleMuX", HLTEleMuX)

        ########################################
        # MC
        ########################################
        if self.isMC:

            self.out.fillBranch("genWeight", event.genWeight)
            self.out.fillBranch("puTrue", event.Pileup_nTrueInt)

            prefire = 1.0
            prefireUp = 1.0
            prefireDown = 1.0

            if hasattr(event, "L1PreFiringWeight_Nom"):
                prefire = event.L1PreFiringWeight_Nom

            if hasattr(event, "L1PreFiringWeight_Up"):
                prefireUp = event.L1PreFiringWeight_Up

            if hasattr(event, "L1PreFiringWeight_Dn"):
                prefireDown = event.L1PreFiringWeight_Dn

            self.out.fillBranch("L1ECALPrefire", prefire)
            self.out.fillBranch("L1ECALPrefireUp", prefireUp)
            self.out.fillBranch("L1ECALPrefireDown", prefireDown)

        ########################################
        # MUONS
        ########################################

        nMu = event.nMuon

        muPt = []
        muEta = []
        muPhi = []
        muEn = []

        muD0 = []
        muDz = []

        muBestTrkPtError = []
        muBestTrkPt = []

        muSIP = []

        muPFChIso03 = []
        muPFPhoIso03 = []
        muPFNeuIso03 = []
        muPFPUIso03 = []

        muCharge = []
        muType = []

        muTrkLayers = []
        muBestTrkType = []

        muPixelHits = []
        muStations = []
        muMatches = []

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

            if hasattr(event, "Muon_bestTrack_ptError"):
                muBestTrkPtError.append(
                    event.Muon_bestTrack_ptError[i]
                )
            else:
                muBestTrkPtError.append(-999.)

            if hasattr(event, "Muon_tunepRelPt"):
                muBestTrkPt.append(
                    event.Muon_tunepRelPt[i]
                )
            else:
                muBestTrkPt.append(pt)

            muSIP.append(event.Muon_sip3d[i])

            ####################################
            # ISO
            ####################################

            chIso = (
                event.Muon_pfRelIso03_chg[i] * pt
            )

            relIso = (
                event.Muon_pfRelIso04_all[i]
            )

            totalIso = relIso * pt

            neuPhoPU = max(0., totalIso - chIso)

            phoIso = 0.5 * neuPhoPU
            neuIso = 0.5 * neuPhoPU
            puIso = 0.

            muPFChIso03.append(chIso)
            muPFPhoIso03.append(phoIso)
            muPFNeuIso03.append(neuIso)
            muPFPUIso03.append(puIso)

            ####################################
            # TYPE
            ####################################

            mtype = 0

            if event.Muon_isGlobal[i]:
                mtype |= (1 << 1)

            if event.Muon_isTracker[i]:
                mtype |= (1 << 2)

            if event.Muon_isPFcand[i]:
                mtype |= (1 << 5)

            muType.append(mtype)

            muCharge.append(event.Muon_charge[i])

            if hasattr(event, "Muon_nTrackerLayers"):
                muTrkLayers.append(
                    event.Muon_nTrackerLayers[i]
                )
            else:
                muTrkLayers.append(-1)

            if hasattr(event, "Muon_bestTrackType"):
                muBestTrkType.append(
                    event.Muon_bestTrackType[i]
                )
            else:
                muBestTrkType.append(-1)

            muPixelHits.append(-1)

            muStations.append(
                event.Muon_nStations[i]
            )

            muMatches.append(-1)

        self.out.fillBranch("nMu", nMu)

        self.out.fillBranch("muPt", muPt)
        self.out.fillBranch("muEta", muEta)
        self.out.fillBranch("muPhi", muPhi)
        self.out.fillBranch("muEn", muEn)

        self.out.fillBranch("muD0", muD0)
        self.out.fillBranch("muDz", muDz)

        self.out.fillBranch(
            "muBestTrkPtError",
            muBestTrkPtError
        )

        self.out.fillBranch(
            "muBestTrkPt",
            muBestTrkPt
        )

        self.out.fillBranch("muSIP", muSIP)

        self.out.fillBranch(
            "muPFChIso03",
            muPFChIso03
        )

        self.out.fillBranch(
            "muPFPhoIso03",
            muPFPhoIso03
        )

        self.out.fillBranch(
            "muPFNeuIso03",
            muPFNeuIso03
        )

        self.out.fillBranch(
            "muPFPUIso03",
            muPFPUIso03
        )

        self.out.fillBranch(
            "muCharge",
            muCharge
        )

        self.out.fillBranch(
            "muType",
            muType
        )

        self.out.fillBranch(
            "muTrkLayers",
            muTrkLayers
        )

        self.out.fillBranch(
            "muBestTrkType",
            muBestTrkType
        )

        self.out.fillBranch(
            "muPixelHits",
            muPixelHits
        )

        self.out.fillBranch(
            "muStations",
            muStations
        )

        self.out.fillBranch(
            "muMatches",
            muMatches
        )

        ########################################
        # PHOTONS
        ########################################

        nPho = event.nPhoton

        phoE = []
        phoEt = []
        phoCalibEt = []

        phoEta = []
        phoPhi = []

        phoSCEta = []
        phoSCPhi = []

        phoIDMVA = []
        phoEleVeto = []

        phoSCRawE = []

        phoSigmaIEtaIEtaFull5x5 = []
        phoSCEtaWidth = []
        phoSCPhiWidth = []

        phoPFPhoIso = []
        phoPFChIso = []
        phoPFChWorstIso = []

        phoHoverE = []

        phoTrkIsoHollowConeDR03 = []

        phoCorrR9Full5x5 = []
        phoCorrHggIDMVA = []

        for i in range(nPho):

            pt = event.Photon_pt[i]
            eta = event.Photon_eta[i]
            phi = event.Photon_phi[i]
            mass = 0.

            p4 = ROOT.TLorentzVector()
            p4.SetPtEtaPhiM(pt, eta, phi, mass)

            phoE.append(p4.E())

            phoEt.append(pt)
            phoCalibEt.append(pt)

            phoEta.append(eta)
            phoPhi.append(phi)

            sceta = eta + event.Photon_deltaEtaSC[i]

            phoSCEta.append(sceta)

            phoSCPhi.append(phi)

            phoIDMVA.append(
                event.Photon_mvaID[i]
            )

            phoEleVeto.append(
                event.Photon_electronVeto[i]
            )

            if hasattr(event, "Photon_energyRaw"):
                phoSCRawE.append(
                    event.Photon_energyRaw[i]
                )
            else:
                phoSCRawE.append(p4.E())

            phoSigmaIEtaIEtaFull5x5.append(
                event.Photon_sieie[i]
            )

            phoSCEtaWidth.append(
                event.Photon_etaWidth[i]
            )

            phoSCPhiWidth.append(
                event.Photon_phiWidth[i]
            )

            ####################################
            # ISOLATIONS
            ####################################

            if hasattr(event, "Photon_pfPhoIso03"):
                phoPFPhoIso.append(
                    event.Photon_pfPhoIso03[i]
                )
            else:
                phoPFPhoIso.append(0.)

            if hasattr(event, "Photon_pfChargedIsoPFPV"):
                phoPFChIso.append(
                    event.Photon_pfChargedIsoPFPV[i]
                )
            else:
                phoPFChIso.append(0.)

            if hasattr(event, "Photon_pfChargedIsoWorstVtx"):
                phoPFChWorstIso.append(
                    event.Photon_pfChargedIsoWorstVtx[i]
                )
            else:
                phoPFChWorstIso.append(0.)

            phoHoverE.append(
                event.Photon_hoe[i]
            )

            ####################################
            # TRACK ISO
            ####################################

            if hasattr(
                event,
                "Photon_trkSumPtHollowConeDR03"
            ):
                phoTrkIsoHollowConeDR03.append(
                    event.Photon_trkSumPtHollowConeDR03[i]
                )
            else:
                phoTrkIsoHollowConeDR03.append(0.)

            ####################################
            # R9
            ####################################

            phoCorrR9Full5x5.append(
                event.Photon_r9[i]
            )

            phoCorrHggIDMVA.append(
                event.Photon_mvaID[i]
            )

        self.out.fillBranch("nPho", nPho)

        self.out.fillBranch("phoE", phoE)
        self.out.fillBranch("phoEt", phoEt)
        self.out.fillBranch("phoCalibEt", phoCalibEt)

        self.out.fillBranch("phoEta", phoEta)
        self.out.fillBranch("phoPhi", phoPhi)

        self.out.fillBranch("phoSCEta", phoSCEta)
        self.out.fillBranch("phoSCPhi", phoSCPhi)

        self.out.fillBranch("phoIDMVA", phoIDMVA)
        self.out.fillBranch("phoEleVeto", phoEleVeto)

        self.out.fillBranch("phoSCRawE", phoSCRawE)

        self.out.fillBranch(
            "phoSigmaIEtaIEtaFull5x5",
            phoSigmaIEtaIEtaFull5x5
        )

        self.out.fillBranch(
            "phoSCEtaWidth",
            phoSCEtaWidth
        )

        self.out.fillBranch(
            "phoSCPhiWidth",
            phoSCPhiWidth
        )

        self.out.fillBranch(
            "phoPFPhoIso",
            phoPFPhoIso
        )

        self.out.fillBranch(
            "phoPFChIso",
            phoPFChIso
        )

        self.out.fillBranch(
            "phoPFChWorstIso",
            phoPFChWorstIso
        )

        self.out.fillBranch(
            "phoHoverE",
            phoHoverE
        )

        self.out.fillBranch(
            "phoTrkIsoHollowConeDR03",
            phoTrkIsoHollowConeDR03
        )

        self.out.fillBranch(
            "phoCorrR9Full5x5",
            phoCorrR9Full5x5
        )

        self.out.fillBranch(
            "phoCorrHggIDMVA",
            phoCorrHggIDMVA
        )

        ########################################
        # JETS
        ########################################

        nJet = event.nJet

        jetPt = []
        jetEta = []
        jetPhi = []
        jetEn = []

        jetNHF = []
        jetNEF = []

        jetID = []

        jetCHF = []
        jetCEF = []
        jetMUF = []

        jetNCH = []
        jetNNP = []

        for i in range(nJet):

            pt = event.Jet_pt[i]
            eta = event.Jet_eta[i]
            phi = event.Jet_phi[i]
            mass = event.Jet_mass[i]

            p4 = ROOT.TLorentzVector()
            p4.SetPtEtaPhiM(pt, eta, phi, mass)

            jetPt.append(pt)
            jetEta.append(eta)
            jetPhi.append(phi)
            jetEn.append(p4.E())

            jetNHF.append(event.Jet_neHEF[i])
            jetNEF.append(event.Jet_neEmEF[i])

            jetID.append(event.Jet_jetId[i])

            jetCHF.append(event.Jet_chHEF[i])
            jetCEF.append(event.Jet_chEmEF[i])
            jetMUF.append(event.Jet_muEF[i])

            jetNCH.append(
                event.Jet_chMultiplicity[i]
            )

            jetNNP.append(
                event.Jet_neMultiplicity[i]
            )

        self.out.fillBranch("nJet", nJet)

        self.out.fillBranch("jetPt", jetPt)
        self.out.fillBranch("jetEta", jetEta)
        self.out.fillBranch("jetPhi", jetPhi)
        self.out.fillBranch("jetEn", jetEn)

        self.out.fillBranch("jetNHF", jetNHF)
        self.out.fillBranch("jetNEF", jetNEF)

        self.out.fillBranch("jetID", jetID)

        self.out.fillBranch("jetCHF", jetCHF)
        self.out.fillBranch("jetCEF", jetCEF)
        self.out.fillBranch("jetMUF", jetMUF)

        self.out.fillBranch("jetNCH", jetNCH)
        self.out.fillBranch("jetNNP", jetNNP)

        ########################################
        # GEN PARTICLES
        ########################################

        if self.isMC:

            nMC = event.nGenPart

            mcPID = []
            mcMomPID = []
            mcGMomPID = []

            mcPt = []
            mcEta = []
            mcPhi = []
            mcMass = []

            mcStatusFlag = []

            for i in range(nMC):

                mcPID.append(
                    event.GenPart_pdgId[i]
                )

                motherIdx = (
                    event.GenPart_genPartIdxMother[i]
                )

                momPID = 0
                gmomPID = 0

                if motherIdx >= 0:

                    momPID = (
                        event.GenPart_pdgId[motherIdx]
                    )

                    gmomIdx = (
                        event.GenPart_genPartIdxMother[
                            motherIdx
                        ]
                    )

                    if gmomIdx >= 0:
                        gmomPID = (
                            event.GenPart_pdgId[gmomIdx]
                        )

                mcMomPID.append(momPID)
                mcGMomPID.append(gmomPID)

                mcPt.append(
                    event.GenPart_pt[i]
                )

                mcEta.append(
                    event.GenPart_eta[i]
                )

                mcPhi.append(
                    event.GenPart_phi[i]
                )

                mcMass.append(
                    event.GenPart_mass[i]
                )

                mcStatusFlag.append(
                    event.GenPart_statusFlags[i]
                )

            self.out.fillBranch("nMC", nMC)

            self.out.fillBranch("mcPID", mcPID)
            self.out.fillBranch("mcMomPID", mcMomPID)
            self.out.fillBranch("mcGMomPID", mcGMomPID)

            self.out.fillBranch("mcPt", mcPt)
            self.out.fillBranch("mcEta", mcEta)
            self.out.fillBranch("mcPhi", mcPhi)
            self.out.fillBranch("mcMass", mcMass)

            self.out.fillBranch(
                "mcStatusFlag",
                mcStatusFlag
            )

        return True
