import ROOT
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module


class xAnaProducer(Module):

    def __init__(self, isMC=True):
        self.isMC = isMC


        self.isMC = isMC
        ####################################
        # PRINT TRIGGER WARNING ONLY ONCE
        ####################################
        self.triggerWarningPrinted = False


    ########################################
    # BEGIN FILE
    ########################################
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):

        self.out = wrappedOutputTree

        ####################################
        # EVENT
        ####################################
        self.out.branch("run", "I")
        self.out.branch("luminosityBlock", "I")
        self.out.branch("event", "L")

        self.out.branch("rho", "F")

        #################################### # TRIGGER ####################################
        self.out.branch( "HLT_Mu17_Photon30_IsoCaloId", "O" )


        if self.isMC:
            self.out.branch("genWeight", "F")
            self.out.branch("Pileup_nTrueInt", "F")

        ####################################
        # MUONS
        ####################################
        self.out.branch("nMu", "I")

        self.out.branch("muPt", "F", lenVar="nMu")
        self.out.branch("muEta", "F", lenVar="nMu")
        self.out.branch("muPhi", "F", lenVar="nMu")
        self.out.branch("muCharge", "I", lenVar="nMu")

        self.out.branch("muD0", "F", lenVar="nMu")
        self.out.branch("muDz", "F", lenVar="nMu")

        self.out.branch("muSIP", "F", lenVar="nMu")

        self.out.branch("muRelIso", "F", lenVar="nMu")

        ####################################
        # PHOTONS
        ####################################
        self.out.branch("nPho", "I")

        self.out.branch("phoPt", "F", lenVar="nPho")
        self.out.branch("phoEta", "F", lenVar="nPho")
        self.out.branch("phoPhi", "F", lenVar="nPho")

        self.out.branch("phoR9", "F", lenVar="nPho")
        self.out.branch("phoHoverE", "F", lenVar="nPho")

        self.out.branch("phoSieie", "F", lenVar="nPho")

        self.out.branch("phoMVAID", "F", lenVar="nPho")

        self.out.branch("phoEleVeto", "I", lenVar="nPho")

        ####################################
        # JETS
        ####################################
        self.out.branch("nJet", "I")

        self.out.branch("jetPt", "F", lenVar="nJet")
        self.out.branch("jetEta", "F", lenVar="nJet")
        self.out.branch("jetPhi", "F", lenVar="nJet")

        ####################################
        # GEN PARTICLES
        ####################################
        if self.isMC:

            self.out.branch("nGenPart", "I")

            self.out.branch("genPID", "I", lenVar="nGenPart")

            self.out.branch("genPt", "F", lenVar="nGenPart")
            self.out.branch("genEta", "F", lenVar="nGenPart")
            self.out.branch("genPhi", "F", lenVar="nGenPart")

    ########################################
    # ANALYZE
    ########################################
    def analyze(self, event):

        ####################################
        # BASIC EVENT CUT
        ####################################

        if event.PV_npvsGood < 1:
            return False

        ####################################
        # TRIGGER
        ####################################


        triggerName = ( "HLT_Mu17_Photon30_IsoCaloId" )

        if not hasattr(event, triggerName):
            if not self.triggerWarningPrinted:
                print( "\033[91m" + f"[WARNING] Trigger {triggerName} NOT found in this dataset!" + "\033[0m" )
                self.triggerWarningPrinted = True
            return False

        passTrig = getattr(event, triggerName)

        #passTrig = (
        #    getattr(event, "HLT_Mu17_Photon30_IsoCaloId", False)
        #    or getattr(event, "HLT_Mu17_Photon30_CaloIdL_L1ISO", False)
        #)

        self.out.fillBranch( "HLT_Mu17_Photon30_IsoCaloId", passTrig )

        if not passTrig:
            return False

        ####################################
        # EVENT INFO
        ####################################

        self.out.fillBranch("run", event.run)
        self.out.fillBranch(
            "luminosityBlock",
            event.luminosityBlock
        )

        self.out.fillBranch("event", event.event)

        self.out.fillBranch(
            "rho",
            event.Rho_fixedGridRhoFastjetAll
        )

        if self.isMC:

            self.out.fillBranch(
                "genWeight",
                event.genWeight
            )

            self.out.fillBranch(
                "Pileup_nTrueInt",
                event.Pileup_nTrueInt
            )

        ####################################
        # MUONS
        ####################################

        muPt = []
        muEta = []
        muPhi = []
        muCharge = []

        muD0 = []
        muDz = []

        muSIP = []

        muRelIso = []

        for i in range(event.nMuon):

            if event.Muon_pt[i] < 5:
                continue

            if abs(event.Muon_eta[i]) > 2.4:
                continue

            muPt.append(event.Muon_pt[i])
            muEta.append(event.Muon_eta[i])
            muPhi.append(event.Muon_phi[i])

            muCharge.append(
                event.Muon_charge[i]
            )

            muD0.append(event.Muon_dxy[i])
            muDz.append(event.Muon_dz[i])

            muSIP.append(
                event.Muon_sip3d[i]
            )

            muRelIso.append(
                event.Muon_pfRelIso04_all[i]
            )

        ####################################
        # REQUIRE TWO MUONS
        ####################################

        if len(muPt) < 2:
            return False

        ####################################
        # PHOTONS
        ####################################

        phoPt = []
        phoEta = []
        phoPhi = []

        phoR9 = []
        phoHoverE = []

        phoSieie = []

        phoMVAID = []

        phoEleVeto = []

        for i in range(event.nPhoton):

            if event.Photon_pt[i] < 10:
                continue

            if abs(event.Photon_eta[i]) > 2.5:
                continue

            phoPt.append(event.Photon_pt[i])

            phoEta.append(
                event.Photon_eta[i]
            )

            phoPhi.append(
                event.Photon_phi[i]
            )

            phoR9.append(
                event.Photon_r9[i]
            )

            phoHoverE.append(
                event.Photon_hoe[i]
            )

            phoSieie.append(
                event.Photon_sieie[i]
            )

            phoMVAID.append(
                event.Photon_mvaID[i]
            )

            phoEleVeto.append(
                event.Photon_electronVeto[i]
            )

        ####################################
        # REQUIRE PHOTON
        ####################################

        if len(phoPt) < 1:
            return False

        ####################################
        # JETS
        ####################################

        jetPt = []
        jetEta = []
        jetPhi = []

        for i in range(event.nJet):

            if event.Jet_pt[i] < 20:
                continue

            jetPt.append(event.Jet_pt[i])

            jetEta.append(
                event.Jet_eta[i]
            )

            jetPhi.append(
                event.Jet_phi[i]
            )

        ####################################
        # GEN PARTICLES
        ####################################

        if self.isMC:

            genPID = []

            genPt = []
            genEta = []
            genPhi = []

            for i in range(event.nGenPart):

                genPID.append(
                    event.GenPart_pdgId[i]
                )

                genPt.append(
                    event.GenPart_pt[i]
                )

                genEta.append(
                    event.GenPart_eta[i]
                )

                genPhi.append(
                    event.GenPart_phi[i]
                )

        ####################################
        # FILL TREE
        ####################################

        self.out.fillBranch("nMu", len(muPt))

        self.out.fillBranch("muPt", muPt)
        self.out.fillBranch("muEta", muEta)
        self.out.fillBranch("muPhi", muPhi)

        self.out.fillBranch(
            "muCharge",
            muCharge
        )

        self.out.fillBranch("muD0", muD0)
        self.out.fillBranch("muDz", muDz)

        self.out.fillBranch("muSIP", muSIP)

        self.out.fillBranch(
            "muRelIso",
            muRelIso
        )

        ####################################

        self.out.fillBranch("nPho", len(phoPt))

        self.out.fillBranch("phoPt", phoPt)
        self.out.fillBranch("phoEta", phoEta)
        self.out.fillBranch("phoPhi", phoPhi)

        self.out.fillBranch("phoR9", phoR9)

        self.out.fillBranch(
            "phoHoverE",
            phoHoverE
        )

        self.out.fillBranch(
            "phoSieie",
            phoSieie
        )

        self.out.fillBranch(
            "phoMVAID",
            phoMVAID
        )

        self.out.fillBranch(
            "phoEleVeto",
            phoEleVeto
        )

        ####################################

        self.out.fillBranch("nJet", len(jetPt))

        self.out.fillBranch("jetPt", jetPt)
        self.out.fillBranch("jetEta", jetEta)
        self.out.fillBranch("jetPhi", jetPhi)

        ####################################

        if self.isMC:

            self.out.fillBranch(
                "nGenPart",
                len(genPID)
            )

            self.out.fillBranch(
                "genPID",
                genPID
            )

            self.out.fillBranch(
                "genPt",
                genPt
            )

            self.out.fillBranch(
                "genEta",
                genEta
            )

            self.out.fillBranch(
                "genPhi",
                genPhi
            )

        return True
